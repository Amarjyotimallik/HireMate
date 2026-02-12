"""
Metrics Service

Computes behavioral metrics from logged events.
All computations happen AFTER task completion - never during.
"""

from datetime import datetime
from typing import List, Dict, Optional
from statistics import stdev, mean

from bson import ObjectId

from app.db import (
    get_events_collection,
    get_attempts_collection,
    get_tasks_collection,
    get_metrics_collection,
)
from app.schemas import (
    EventType,
    AttemptStatus,
    RiskLevel,
    ComputedMetricsResponse,
    GlobalMetrics,
    PerTaskMetrics,
    AggregatedPatterns,
    RiskPreference,
)
from app.utils import analyze_reasoning
from app.core import AttemptNotFoundError, AttemptLockedError
from app.config import get_settings


# Current version of metrics computation logic
METRICS_VERSION = "1.0.0"


async def compute_metrics(attempt_id: str, force_recompute: bool = False) -> ComputedMetricsResponse:
    """
    Compute all behavioral metrics for a completed assessment.
    
    This is called AFTER the assessment is completed.
    """
    attempts = get_attempts_collection()
    metrics_coll = get_metrics_collection()
    
    # Verify attempt exists and is completed
    attempt = await attempts.find_one({"_id": ObjectId(attempt_id)})
    if not attempt:
        raise AttemptNotFoundError("Assessment not found")
    
    if attempt["status"] not in [AttemptStatus.COMPLETED.value, AttemptStatus.LOCKED.value]:
        raise AttemptLockedError("Assessment must be completed before computing metrics")
    
    # Check if already computed
    if not force_recompute:
        existing = await metrics_coll.find_one({"attempt_id": attempt_id})
        if existing:
            return _metrics_doc_to_response(existing)
    
    # Get all events for this attempt
    events = get_events_collection()
    cursor = events.find({"attempt_id": attempt_id}).sort("sequence_number", 1)
    event_list = await cursor.to_list(length=10000)
    
    # Get task details for risk level mapping
    tasks = get_tasks_collection()
    task_map = await _build_task_map(attempt["task_ids"], tasks)
    
    # Compute per-task metrics
    per_task_metrics = await _compute_per_task_metrics(
        event_list, task_map, attempt["task_ids"]
    )
    
    # Compute global metrics
    global_metrics = _compute_global_metrics(
        attempt, per_task_metrics
    )
    
    # Compute aggregated patterns
    aggregated_patterns = _compute_aggregated_patterns(per_task_metrics)
    
    # Store metrics
    now = datetime.utcnow()
    metrics_doc = {
        "attempt_id": attempt_id,
        "computed_at": now,
        "version": METRICS_VERSION,
        "global_metrics": global_metrics.model_dump(),
        "per_task_metrics": [m.model_dump() for m in per_task_metrics],
        "aggregated_patterns": aggregated_patterns.model_dump(),
    }
    
    # Upsert (replace if exists due to force_recompute)
    await metrics_coll.update_one(
        {"attempt_id": attempt_id},
        {"$set": metrics_doc},
        upsert=True
    )
    
    # Get the stored document to return with ID
    stored = await metrics_coll.find_one({"attempt_id": attempt_id})
    return _metrics_doc_to_response(stored)


async def get_metrics(attempt_id: str) -> Optional[ComputedMetricsResponse]:
    """Get computed metrics for an attempt."""
    metrics_coll = get_metrics_collection()
    
    metrics = await metrics_coll.find_one({"attempt_id": attempt_id})
    if not metrics:
        return None
    
    return _metrics_doc_to_response(metrics)


async def _build_task_map(task_ids: List[str], tasks) -> Dict:
    """Build a map of task_id to task details."""
    object_ids = [ObjectId(tid) for tid in task_ids]
    cursor = tasks.find({"_id": {"$in": object_ids}})
    
    task_map = {}
    async for task in cursor:
        task_id = str(task["_id"])
        option_map = {opt["id"]: opt for opt in task["options"]}
        task_map[task_id] = {
            "title": task["title"],
            "options": option_map,
        }
    
    return task_map


async def _compute_per_task_metrics(
    events: List[Dict],
    task_map: Dict,
    task_ids: List[str],
) -> List[PerTaskMetrics]:
    """Compute metrics for each task."""
    settings = get_settings()
    idle_threshold = settings.idle_threshold_ms
    
    # Group events by task
    task_events = {}
    for event in events:
        task_id = event["task_id"]
        if task_id not in task_events:
            task_events[task_id] = []
        task_events[task_id].append(event)
    
    per_task = []
    
    for task_id in task_ids:
        if task_id not in task_events:
            continue
        
        events_for_task = task_events[task_id]
        task_info = task_map.get(task_id, {})
        
        # Find key events
        task_started = None
        task_completed = None
        first_selection = None
        last_selection = None
        reasoning_submitted = None
        option_changes = 0
        idle_events = []
        focus_loss_count = 0
        
        for event in events_for_task:
            event_type = event["event_type"]
            
            if event_type == EventType.TASK_STARTED.value:
                task_started = event
            elif event_type == EventType.TASK_COMPLETED.value:
                task_completed = event
            elif event_type == EventType.OPTION_SELECTED.value:
                if first_selection is None:
                    first_selection = event
                last_selection = event
            elif event_type == EventType.OPTION_CHANGED.value:
                option_changes += 1
                last_selection = event
            elif event_type == EventType.REASONING_SUBMITTED.value:
                reasoning_submitted = event
            elif event_type == EventType.IDLE_DETECTED.value:
                idle_events.append(event)
            elif event_type == EventType.FOCUS_LOST.value:
                focus_loss_count += 1
        
        # Calculate time metrics
        if task_started and task_completed:
            time_spent = (task_completed["timestamp"] - task_started["timestamp"]).total_seconds()
        else:
            time_spent = 0.0
        
        if task_started and first_selection:
            first_decision_speed = (first_selection["timestamp"] - task_started["timestamp"]).total_seconds()
            hesitation = first_decision_speed
        else:
            first_decision_speed = time_spent
            hesitation = time_spent
        
        # Calculate idle time
        idle_time = sum(
            event["payload"].get("idle_duration_ms", 0) / 1000
            for event in idle_events
        )
        
        # Get final option and risk level
        final_option_id = ""
        final_risk_level = RiskLevel.MEDIUM
        
        if task_completed and "final_option_id" in task_completed["payload"]:
            final_option_id = task_completed["payload"]["final_option_id"]
        elif last_selection:
            if "to_option_id" in last_selection["payload"]:
                final_option_id = last_selection["payload"]["to_option_id"]
            elif "option_id" in last_selection["payload"]:
                final_option_id = last_selection["payload"]["option_id"]
        
        if final_option_id and task_info.get("options"):
            option_info = task_info["options"].get(final_option_id, {})
            if "risk_level" in option_info:
                final_risk_level = RiskLevel(option_info["risk_level"])
        
        # Analyze reasoning
        reasoning_text = ""
        if reasoning_submitted and "final_text" in reasoning_submitted["payload"]:
            reasoning_text = reasoning_submitted["payload"]["final_text"]
        
        reasoning_analysis = analyze_reasoning(reasoning_text)
        
        per_task.append(PerTaskMetrics(
            task_id=task_id,
            time_spent_seconds=round(time_spent, 2),
            hesitation_seconds=round(hesitation, 2),
            first_decision_speed_seconds=round(first_decision_speed, 2),
            decision_change_count=option_changes,
            final_option_id=final_option_id,
            final_option_risk_level=final_risk_level,
            reasoning_depth_score=reasoning_analysis["depth_score"],
            reasoning_word_count=reasoning_analysis["word_count"],
            reasoning_logical_keywords_count=reasoning_analysis["keyword_count"],
            idle_time_seconds=round(idle_time, 2),
            focus_loss_count=focus_loss_count,
        ))
    
    return per_task


def _compute_global_metrics(
    attempt: Dict,
    per_task_metrics: List[PerTaskMetrics],
) -> GlobalMetrics:
    """Compute global metrics across all tasks."""
    if not per_task_metrics:
        return GlobalMetrics(
            total_time_seconds=0,
            active_interaction_time_seconds=0,
            hesitation_time_seconds=0,
            total_tasks=len(attempt["task_ids"]),
            tasks_completed=0,
            avg_time_per_task_seconds=0,
        )
    
    total_time = sum(m.time_spent_seconds for m in per_task_metrics)
    total_hesitation = sum(m.hesitation_seconds for m in per_task_metrics)
    total_idle = sum(m.idle_time_seconds for m in per_task_metrics)
    
    # Active time = total time - hesitation - idle
    active_time = max(0, total_time - total_idle)
    
    # Use attempt timestamps if available
    if attempt.get("started_at") and attempt.get("completed_at"):
        actual_total = (attempt["completed_at"] - attempt["started_at"]).total_seconds()
        total_time = actual_total
        active_time = max(0, actual_total - total_idle)
    
    tasks_completed = len(per_task_metrics)
    avg_time = total_time / tasks_completed if tasks_completed > 0 else 0
    
    return GlobalMetrics(
        total_time_seconds=round(total_time, 2),
        active_interaction_time_seconds=round(active_time, 2),
        hesitation_time_seconds=round(total_hesitation, 2),
        total_tasks=len(attempt["task_ids"]),
        tasks_completed=tasks_completed,
        avg_time_per_task_seconds=round(avg_time, 2),
    )


def _compute_aggregated_patterns(
    per_task_metrics: List[PerTaskMetrics],
) -> AggregatedPatterns:
    """Compute aggregated behavioral patterns."""
    if not per_task_metrics:
        return AggregatedPatterns(
            risk_preference=RiskPreference(),
            decision_consistency=0.5,
            reasoning_engagement=0.0,
            attention_stability=1.0,
        )
    
    # Risk preference analysis
    risk_counts = {"low": 0, "medium": 0, "high": 0}
    for m in per_task_metrics:
        risk_counts[m.final_option_risk_level.value] += 1
    
    total = sum(risk_counts.values())
    if total > 0:
        if risk_counts["low"] > total * 0.6:
            dominant = "low"
        elif risk_counts["high"] > total * 0.6:
            dominant = "high"
        elif abs(risk_counts["low"] - risk_counts["high"]) < total * 0.2:
            dominant = "balanced"
        else:
            dominant = "medium"
    else:
        dominant = "balanced"
    
    risk_preference = RiskPreference(
        low_count=risk_counts["low"],
        medium_count=risk_counts["medium"],
        high_count=risk_counts["high"],
        dominant=dominant,
    )
    
    # Decision consistency (based on decision time variance)
    decision_times = [m.first_decision_speed_seconds for m in per_task_metrics]
    if len(decision_times) > 1 and mean(decision_times) > 0:
        cv = stdev(decision_times) / mean(decision_times)
        decision_consistency = max(0, min(1, 1 - cv))
    else:
        decision_consistency = 0.5
    
    # Reasoning engagement (average depth score)
    depth_scores = [m.reasoning_depth_score for m in per_task_metrics]
    reasoning_engagement = mean(depth_scores) if depth_scores else 0.0
    
    # Attention stability (inverse of focus loss rate)
    total_focus_losses = sum(m.focus_loss_count for m in per_task_metrics)
    num_tasks = len(per_task_metrics)
    avg_focus_loss = total_focus_losses / num_tasks if num_tasks > 0 else 0
    # Cap at 5 focus losses per task as max instability
    attention_stability = max(0, 1 - (avg_focus_loss / 5))
    
    return AggregatedPatterns(
        risk_preference=risk_preference,
        decision_consistency=round(decision_consistency, 3),
        reasoning_engagement=round(reasoning_engagement, 3),
        attention_stability=round(attention_stability, 3),
    )


def _metrics_doc_to_response(doc: Dict) -> ComputedMetricsResponse:
    """Convert MongoDB document to response schema."""
    return ComputedMetricsResponse(
        id=str(doc["_id"]),
        attempt_id=doc["attempt_id"],
        computed_at=doc["computed_at"],
        version=doc["version"],
        global_metrics=GlobalMetrics(**doc["global_metrics"]),
        per_task_metrics=[PerTaskMetrics(**m) for m in doc["per_task_metrics"]],
        aggregated_patterns=AggregatedPatterns(**doc["aggregated_patterns"]),
    )
