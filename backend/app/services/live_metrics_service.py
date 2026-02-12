"""
Live Metrics Service

Computes real-time behavioral metrics during active assessments.
Includes skill profile (radar chart), behavioral summary, recruiter view,
candidate insights, and decision path analysis based on idea.md formulas.
"""

from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter

from bson import ObjectId

from app.db import (
    get_events_collection,
    get_attempts_collection,
    get_tasks_collection,
)
from app.schemas import (
    EventType,
    AttemptStatus,
    RiskLevel,
)
from app.config import get_settings

# Population Intelligence imports
from app.services.population_stats_service import (
    get_all_percentiles,
    get_confidence_intervals,
    compute_behavioral_consistency,  # Renamed from compute_authenticity_score
    get_population_context,
    update_population_stats,
)
from app.services.false_positive_protection import get_false_positive_protection


# ============================================================================
# THRESHOLDS (refined for defensibility - see behavioral_system_refinement.md)
# ============================================================================
THRESHOLDS = {
    # Time thresholds (in seconds) - adjusted to reduce false positives
    "fast_decision": 15,        # < 15s = quick selection (was 10s)
    "slow_decision": 45,        # > 45s = extended deliberation (was 30s)
    "very_slow_decision": 90,   # > 90s = very extended (was 60s)
    
    # Idle time (renamed from hesitation - describes observable pause, not mental state)
    "low_idle_ratio": 0.2,      # < 20% idle time
    "high_idle_ratio": 0.5,     # > 50% idle time
    
    # Decision changes - raised threshold to reduce false exploratory labels
    "low_changes": 1,
    "high_changes": 4,          # was 3
    
    # Reasoning (explanation detail - word count normalized)
    "brief_explanation": 20,    # < 20 words
    "detailed_explanation": 40, # > 40 words (was 50 - lower verbosity requirement)
    "connector_usage_threshold": 40,  # renamed from structured_reasoning_score
    
    # Coverage
    "full_coverage_ratio": 0.8      # Viewed 80%+ of options
}

LOGICAL_KEYWORDS = [
    "because", "therefore", "however", "although", "considering",
    "firstly", "secondly", "finally", "in contrast", "as a result",
    "given that", "on the other hand", "weighing", "analyzing",
    "since", "thus", "hence", "moreover", "furthermore"
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def _selection_speed_to_frontend_label(backend_label: str) -> str:
    """
    Convert internal selection speed labels to frontend-expected labels.
    Quick → High (fast selection speed is "high")
    Moderate → Moderate
    Extended → Low (slow selection speed is "low")
    """
    mapping = {
        "Quick": "High",
        "Moderate": "Moderate", 
        "Extended": "Low",
        "N/A": "N/A"
    }
    return mapping.get(backend_label, backend_label)


def _generate_metric_explanations(
    aggregate_metrics: Dict,
    behavioral_summary: Dict,
    skill_profile: Dict,
    tasks_completed: int,
    total_tasks: int
) -> Dict:
    """
    Generate evidence-based explanations for each metric.
    
    These explanations show the recruiter WHY a metric has its value,
    including raw data and threshold comparisons.
    
    Example: "Selection Speed: High because candidate selected options 
              in 8.2s avg (threshold: <15s = High)"
    """
    explanations = {}
    
    # --- Avg Response Time Explanation ---
    avg_selection = aggregate_metrics.get("avg_initial_selection", 0)
    if avg_selection > 0:
        explanations["avg_response_time"] = (
            f"Avg first-click time = mean(first_click_seconds) across {tasks_completed} questions: {avg_selection:.1f}s."
        )
    
    # --- Selection Speed Explanation ---
    speed_label = aggregate_metrics.get("selection_speed_label", "N/A")
    
    if avg_selection > 0:
        speed_label_frontend = _selection_speed_to_frontend_label(speed_label)
        explanations["selection_speed"] = (
            f"Label uses avg first-click time: Quick < {THRESHOLDS['fast_decision']}s, "
            f"Moderate {THRESHOLDS['fast_decision']}-{THRESHOLDS['slow_decision']}s, "
            f"Extended > {THRESHOLDS['slow_decision']}s. Current avg: {avg_selection:.1f}s → {speed_label_frontend}."
        )
    
    # --- Idle Time Explanation ---
    avg_idle = aggregate_metrics.get("avg_idle_time", 0)
    if avg_idle < 5:
        idle_level = "Low"
    elif avg_idle < 15:
        idle_level = "Moderate"
    else:
        idle_level = "High"
    
    explanations["idle_time"] = (
        f"Avg idle before first click = total_idle_seconds / questions: {avg_idle:.1f}s. "
        f"Level: {idle_level} (<5s Low, 5–15s Moderate, >15s High)."
    )
    
    # --- Session Continuity Explanation ---
    total_changes = aggregate_metrics.get("total_changes", 0)
    avg_changes = total_changes / tasks_completed if tasks_completed > 0 else 0
    continuity = max(0, 100 - min(100, total_changes * 15))
    
    explanations["session_continuity"] = (
        f"Session continuity = 100 − min(100, total_changes × 15). "
        f"Total changes: {total_changes} (avg {avg_changes:.1f}/question) → {continuity}%."
    )
    if continuity >= 80:
        explanations["session_continuity"] += " High continuity."
    elif continuity >= 50:
        explanations["session_continuity"] += " Moderate continuity."
    else:
        explanations["session_continuity"] += " Low continuity."

    # --- Decision Firmness Explanation ---
    firmness_penalty = 100 / max(1, THRESHOLDS["high_changes"])
    decision_firmness = max(0, 100 - min(100, avg_changes * firmness_penalty))
    explanations["decision_firmness"] = (
        f"Decision firmness = 100 − min(100, avg_changes × {firmness_penalty:.1f}). "
        f"Avg changes: {avg_changes:.1f} → {decision_firmness:.0f}%."
    )
    if decision_firmness >= 80:
        explanations["decision_firmness"] += " High stability."
    elif decision_firmness >= 50:
        explanations["decision_firmness"] += " Moderate stability."
    else:
        explanations["decision_firmness"] += " Low stability."
    
    # --- Approach Pattern Explanation ---
    approach = behavioral_summary.get("approach_pattern", "")
    pattern_dist = behavioral_summary.get("pattern_distribution", {})
    confidence = behavioral_summary.get("confidence_level", 0)
    questions_analyzed = behavioral_summary.get("questions_analyzed", 0)
    dominant_pattern = behavioral_summary.get("dominant_pattern", "")
    dominant_percentage = behavioral_summary.get("dominant_percentage", 0)
    
    if approach and "Analyzing" not in str(approach):
        pattern_breakdown = ", ".join([f"{k}: {v}%" for k, v in pattern_dist.items()]) if pattern_dist else "N/A"
        
        pattern_descriptions = {
            "Direct": "made quick selections with few revisions",
            "Iterative": "revised their answers multiple times before finalizing",
            "Deliberative": "took extended time with detailed explanations",
            "Balanced": "showed a mix of decision-making styles"
        }
        
        # Remove asterisk for lookup
        clean_approach = approach.replace("*", "")
        description = pattern_descriptions.get(clean_approach, "showed varying patterns")
        
        explanations["approach_pattern"] = (
            f"Pattern mix from {questions_analyzed} completed questions: {pattern_breakdown}. "
            f"Dominant: {dominant_pattern} ({dominant_percentage}%). Confidence: {confidence}%."
        )
        if "*" in str(approach):
            explanations["approach_pattern"] += " Preliminary due to limited data."
    else:
        explanations["approach_pattern"] = (
            f"Need at least 2 completed questions. Currently analyzed: {questions_analyzed}."
        )
    
    # --- Behavioral Mode / Approach Explanation ---
    mode = behavioral_summary.get("behavioral_mode", "") or behavioral_summary.get("approach", "")
    avg_idle = aggregate_metrics.get("avg_idle_time", 0)
    
    mode_explanations = {
        "Efficiency-focused": "The candidate prioritizes speed and decisiveness, quickly committing to selections.",
        "Detail-oriented": "The candidate takes time to carefully consider options and provides thorough explanations.",
        "Exploration-focused": "The candidate explores multiple options before settling, indicating thorough evaluation.",
        "Adaptive": "The candidate adjusts their approach based on the question, showing flexibility."
    }
    
    if mode and mode in mode_explanations:
        explanations["approach"] = (
            f"Approach derives from dominant pattern mapping (Direct→Efficiency-focused, "
            f"Iterative→Exploration-focused, Deliberative→Detail-oriented, Balanced→Adaptive). "
            f"Current mode: {mode}."
        )
    elif mode and "Analyzing" in str(mode):
        explanations["approach"] = (
            f"Still analyzing. Sample size: {questions_analyzed} question(s)."
        )
    
    # --- Under Pressure Explanation ---
    pressure = behavioral_summary.get("under_pressure", "")
    
    pressure_explanations = {
        "Steady progression": "The candidate maintained a consistent pace throughout, suggesting comfortable engagement.",
        "Variable pacing": "Timing varied across questions - some answered quickly, others took longer.",
        "Frequent revisions": "Multiple answer changes suggest the candidate may be uncertain or thoroughly exploring options.",
        "Consistent approach": "The candidate showed stable behavior patterns across all questions."
    }
    
    if pressure:
        explanations["under_pressure"] = (
            f"{pressure_explanations.get(pressure, f'Observed pattern: {pressure}.')} "
            f"Rules: avg idle >15s & total changes >3 ⇒ Variable pacing; "
            f"changes/question >3 ⇒ Frequent revisions; dominant Direct ⇒ Steady progression; else Consistent approach. "
            f"Current: avg idle {avg_idle:.1f}s, changes/question {avg_changes:.1f}."
        )
    
    # --- Analysis Confidence Explanation ---
    if questions_analyzed:
        base_confidence = (
            25 if questions_analyzed == 1 else
            50 if questions_analyzed == 2 else
            75 if questions_analyzed == 3 else
            min(95, 75 + (questions_analyzed - 3) * 5)
        )
        boosted = dominant_percentage >= 70
        explanations["analysis_confidence"] = (
            f"Confidence = base by sample size (1→25, 2→50, 3→75, 4+→75+5×(n−3), cap 95) "
            f"+ 10 if dominant ≥ 70%. Current: base {base_confidence} + "
            f"{'10' if boosted else '0'} = {confidence}%."
        )
    
    # --- Radar Chart Dimensions Explanations ---
    if skill_profile:
        task_completion = skill_profile.get("task_completion", skill_profile.get("problem_solving", 0))
        explanations["task_completion"] = (
            f"Score: {task_completion}%. Completed {tasks_completed}/{total_tasks} questions."
        )
        
        selection_speed_score = skill_profile.get("selection_speed", skill_profile.get("decision_speed", 0))
        explanations["selection_speed_score"] = (
            f"Score: {selection_speed_score}%. Avg first click: {avg_selection:.1f}s."
        )
        
        deliberation_pattern = skill_profile.get("deliberation_pattern", skill_profile.get("analytical_thinking", 0))
        explanations["deliberation_pattern"] = (
            f"Score: {deliberation_pattern}%. Based on explanation depth and completion rate."
        )
        
        option_exploration = skill_profile.get("option_exploration", skill_profile.get("creativity", 0))
        explanations["option_exploration"] = (
            f"Score: {option_exploration}%. Based on options viewed and revisions."
        )
        
        risk_preference = skill_profile.get("risk_preference", skill_profile.get("risk_assessment", 0))
        explanations["risk_preference"] = (
            f"Score: {risk_preference}%. Based on timing and choice patterns."
        )

    # --- Behavioral Consistency Explanation ---
    focus_loss = aggregate_metrics.get("focus_loss_count", 0)
    pastes = aggregate_metrics.get("paste_count", 0)
    copies = aggregate_metrics.get("copy_count", 0)
    idles = aggregate_metrics.get("long_idle_count", 0)
    
    # Calculate resilience for explanation matching - aligned with _compute_aggregate_metrics
    resilience_exp = max(0, 100 - (focus_loss * 10) - (pastes * 20) - (copies * 5))
    
    reasons_list = []
    if focus_loss > 0: reasons_list.append(f"{focus_loss} focus loss(es)")
    if pastes > 0: reasons_list.append(f"{pastes} paste(s)")
    if copies > 0: reasons_list.append(f"{copies} copy event(s)")
    if idles > 0: reasons_list.append(f"{idles} long idle(s)")
    
    explanations["behavioral_consistency"] = (
        f"Measures adherence to assessment patterns. Consistency: {resilience_exp:.0f}%. "
        f"Adjusted for: {', '.join(reasons_list) if reasons_list else 'No anomalous patterns detected.'}"
    )
    # Also add for backward compatibility
    explanations["cheating_resilience"] = explanations["behavioral_consistency"]
    
    return explanations


# ============================================================================
# POPULATION INTELLIGENCE (Black-box audit fixes)
# ============================================================================

async def _compute_population_intelligence(
    aggregate_metrics: dict,
    skill_profile: dict,
    per_task_metrics: list,
    tasks_completed: int,
    recruiter_id: str = None,
    anti_cheat_metrics: dict = None
) -> dict:
    """
    Compute population-relative metrics for trust and transparency.
    
    This addresses the black-box audit issues:
    - No baselines → Now shows percentiles ("faster than 78% of candidates")
    - No error bounds → Now shows confidence intervals
    - Can be gamed → Now includes authenticity score
    
    Returns:
        dict with percentiles, confidence_intervals, authenticity, population_context
    """
    # Build a metrics dict for population stats lookup
    metrics_for_lookup = {
        "metrics": {
            "avg_response_time": aggregate_metrics.get("avg_initial_selection", 0),
            "idle_time": aggregate_metrics.get("idle_time_level", 0),
            "session_continuity": max(0, 100 - (aggregate_metrics.get("total_changes", 0) * 15)),
        },
        "aggregate_metrics": aggregate_metrics,
        "skill_profile": skill_profile,
    }
    
    # Get percentiles (how candidate compares to population)
    percentiles = await get_all_percentiles(metrics_for_lookup, recruiter_id)
    
    # Get confidence intervals (uncertainty based on sample size)
    confidence_intervals = await get_confidence_intervals(
        metrics_for_lookup, 
        tasks_completed, 
        recruiter_id
    )
    
    # Compute behavioral consistency analysis - NOT a "cheating detector"
    # This identifies patterns that differ from typical independent problem-solving
    behavioral_consistency = compute_behavioral_consistency(per_task_metrics, anti_cheat_metrics)
    
    # Generate human-readable context
    population_context = await get_population_context(percentiles, recruiter_id)
    
    return {
        "percentiles": percentiles,
        "confidence_intervals": confidence_intervals,
        "behavioral_consistency": behavioral_consistency,
        "authenticity": behavioral_consistency,  # For frontend compatibility
        "population_context": population_context,
        "has_baseline_data": len(percentiles) > 0,
        "sample_size": tasks_completed,
    }


# ============================================================================
# MAIN METRICS COMPUTATION
# ============================================================================
async def compute_live_metrics(attempt_id: str) -> Optional[Dict]:
    """
    Compute comprehensive metrics for an in-progress or completed assessment.
    Includes all behavioral metrics, skill profile, and recruiter insights.
    """
    attempts = get_attempts_collection()
    events_coll = get_events_collection()
    
    # Get attempt
    attempt = await attempts.find_one({"_id": ObjectId(attempt_id)})
    if not attempt:
        return None
    
    # Calculate time elapsed
    started_at = attempt.get("started_at")
    completed_at = attempt.get("completed_at")
    now = datetime.utcnow()
    
    if started_at:
        if completed_at:
            time_elapsed_seconds = (completed_at - started_at).total_seconds()
        else:
            time_elapsed_seconds = (now - started_at).total_seconds()
    else:
        time_elapsed_seconds = 0
    
    # Get total time limit
    total_tasks = len(attempt["task_ids"])
    total_time_seconds = total_tasks * 60  # 1 minute per task default
    time_remaining_seconds = max(0, total_time_seconds - time_elapsed_seconds)
    
    # Get all events for this attempt (support both string and ObjectId for compatibility)
    cursor = events_coll.find({
        "$or": [
            {"attempt_id": attempt_id},            # Real-time events (stored as string)
            {"attempt_id": ObjectId(attempt_id)}   # Seeded demo data (stored as ObjectId)
        ]
    }).sort("sequence_number", 1)
    event_list = await cursor.to_list(length=10000)
    
    # Compute per-task metrics (pass started_at for first task fallback)
    per_task_metrics = await _compute_per_task_metrics(event_list, attempt["task_ids"], started_at)
    
    # Compute aggregate metrics
    aggregate_metrics = _compute_aggregate_metrics(per_task_metrics, time_elapsed_seconds)
    
    # Check if ANY tasks have been completed
    tasks_completed = aggregate_metrics.get("tasks_completed", 0)
    has_real_data = tasks_completed > 0
    
    # Extract recruiter_id for population stats (used for per-recruiter baselines)
    recruiter_id = str(attempt.get("recruiter_id", "")) if attempt.get("recruiter_id") else None
    
    # Compute skill profile (radar chart dimensions) - only if we have real data
    if has_real_data:
        skill_profile = _compute_skill_profile(aggregate_metrics, per_task_metrics)
    else:
        # Return zeros when no tasks completed - don't show misleading defaults
        skill_profile = {
            "problem_solving": 0,
            "decision_speed": 0,
            "analytical_thinking": 0,
            "creativity": 0,
            "risk_assessment": 0,
            "task_completion": 0,
            "selection_speed": 0,
            "deliberation_pattern": 0,
            "option_exploration": 0,
            "risk_preference": 0,
        }
    
    # Compute behavioral summary
    total_tasks = len(attempt["task_ids"])
    is_completed = tasks_completed >= total_tasks
    
    if not has_real_data:
        # No completed tasks - return explicit 'waiting' state
        behavioral_summary = {
            "decision_style": None,
            "approach_pattern": None,
            "approach": None,
            "behavioral_mode": None,
            "under_pressure": None,
            "pressure_pattern": None,
            "verdict": None,
            "change_rate": None,
            "strength": None,
            "improvement_area": None,
            "all_strengths": [],
            "all_improvements": [],
        }
        resume_comparison = {"claims": [], "observed_skills": None, "overall_score": 0}
        candidate_insights = {"strengths": [], "weaknesses": [], "recommendation": "Waiting for data..."}
        role_fit = {"score": 0, "label": "Waiting...", "color": "gray"}
    elif not is_completed:
        # During the test: Calculate progressive metrics with per-task analysis
        intermediate_summary = _compute_behavioral_summary(aggregate_metrics, per_task_metrics)
        
        behavioral_summary = {
            # Live progressive metrics
            "decision_style": intermediate_summary["decision_style"], 
            "approach_pattern": intermediate_summary.get("approach_pattern"),
            "approach": intermediate_summary.get("approach"), 
            "behavioral_mode": intermediate_summary.get("behavioral_mode"),
            "under_pressure": intermediate_summary.get("under_pressure"),
            
            # Hide Verdict until done
            "verdict": None,
            
            "change_rate": intermediate_summary["change_rate"],
            "strength": intermediate_summary["strength"],
            "improvement_area": intermediate_summary["improvement_area"],
            "all_strengths": intermediate_summary["all_strengths"],
            "all_improvements": intermediate_summary["all_improvements"],
            
            # NEW: Progressive analysis fields
            "confidence_level": intermediate_summary.get("confidence_level", 0),
            "pattern_distribution": intermediate_summary.get("pattern_distribution", {}),
            "dominant_pattern": intermediate_summary.get("dominant_pattern"),
            "dominant_percentage": intermediate_summary.get("dominant_percentage", 0),
            "questions_analyzed": intermediate_summary.get("questions_analyzed", 0),
            "analysis_status": intermediate_summary.get("analysis_status", "analyzing"),
        }

        
        # Hide Skills until done
        resume_comparison = {"claims": [], "observed_skills": None, "overall_score": 0}
        
        # Candidate insights pending
        candidate_insights = {"strengths": [], "weaknesses": [], "recommendation": "Analysis in Progress"}
        role_fit = {"score": 0, "label": "Calculating...", "color": "gray"}
    else:
        # Assessment Completed: Show Full Results with progressive analysis
        behavioral_summary = _compute_behavioral_summary(aggregate_metrics, per_task_metrics)
        
        # Override verdict with LLM result if available
        analysis_result = attempt.get("analysis_result")
        if analysis_result and analysis_result.get("verdict"):
            behavioral_summary["verdict"] = analysis_result["verdict"]
            behavioral_summary["verdict_source"] = "AI-assisted behavioral analysis"  # Transparency
            
        candidate_insights = _compute_candidate_insights(behavioral_summary, aggregate_metrics)
        role_fit = _compute_role_fit(skill_profile, aggregate_metrics)
        resume_comparison = _compute_resume_comparison(attempt.get("candidate_info", {}), skill_profile, per_task_metrics)
    
    # Compute decision path
    decision_path = _compute_decision_path(event_list)
    
    # role_fit and resume_comparison are handled in else block or initialized in if block
    # We assign them here to ensure they exist for return

    
    # Build chart data from per-task metrics
    chart_data = []
    for i, task_metrics in enumerate(per_task_metrics):
        chart_data.append({
            "task": i + 1,
            "timeTaken": int(task_metrics.get("time_spent_seconds", 0) * 100),
            "changes": int(task_metrics.get("decision_changes", 0) * 500),
            "decisionSpeed": int(task_metrics.get("initial_selection_seconds", 0) * 100),
            "idleTime": int(task_metrics.get("idle_time_seconds", 0) * 100),  # renamed from hesitation
        })
    
    analysis_log = f"""
    [BEHAVIORAL OBSERVATION] - Attempt: {attempt_id} | Task: {attempt["current_task_index"] + 1}
    ---------------------------------------------------
    > Initial Selection Time: {aggregate_metrics.get("avg_initial_selection")}s ({aggregate_metrics.get("selection_speed_label")})
    > Idle Time (avg):        {aggregate_metrics.get("avg_idle_time")}s
    > Session Continuity:     {100 - min(40, (aggregate_metrics.get("total_changes", 0) * 5))}
    > Reasoning Depth:        {aggregate_metrics.get("reasoning_depth")} (Words: {aggregate_metrics.get("total_explanation_words")})
    > Observed Pattern:       {behavioral_summary.get("approach_pattern")} | Changes: {behavioral_summary.get("change_rate")}
    > Recruiter Summary:      {role_fit.get("recommendation")} (Score: {role_fit.get("overall_score")})
    ---------------------------------------------------
    """
    print(analysis_log)

    # Get current question details for Mirror View
    current_question = await _get_current_question(attempt, event_list)

    return {
        "attempt_id": attempt_id,
        "candidate": {
            "name": attempt["candidate_info"]["name"],
            "email": attempt["candidate_info"]["email"],
            "position": attempt["candidate_info"]["position"],
            "avatar": _get_initials(attempt["candidate_info"]["name"]),
        },
        "progress": {
            "current": attempt["current_task_index"] + 1,
            "total": total_tasks,
            "status": attempt["status"],
        },
        "time_elapsed_seconds": int(time_elapsed_seconds),
        "time_remaining_seconds": int(time_remaining_seconds),
        "metrics": {
            "avg_response_time": round(aggregate_metrics.get("avg_initial_selection", 0), 2) if has_real_data else 0,
            # Idle time as percentage (normalized from idle_time_level 0-100)
            "idle_time": aggregate_metrics.get("idle_time_level", 0) if has_real_data else 0,
            # Selection speed labels - None when no data
            "decision_speed": _selection_speed_to_frontend_label(aggregate_metrics.get("selection_speed_label", "N/A")) if has_real_data else None,
            # Session continuity - 0 when no data (not 100%)
            "session_continuity": max(0, 100 - min(100, (aggregate_metrics.get("total_changes", 0) * 15))) if has_real_data else None,  # None = no data yet, not failure
            # Decision firmness from average selection changes per question
            "decision_firmness": round(
                max(
                    0,
                    100 - min(
                        100,
                        (
                            (aggregate_metrics.get("total_changes", 0) / tasks_completed)
                            if tasks_completed > 0 else 0
                        ) * (100 / max(1, THRESHOLDS["high_changes"]))
                    )
                )
            ),
            # Backward compatibility keys
            "selection_speed": _selection_speed_to_frontend_label(aggregate_metrics.get("selection_speed_label", "N/A")) if has_real_data else None,
            "focus_score": max(0, 100 - min(100, (aggregate_metrics.get("total_changes", 0) * 15))) if has_real_data else 0,
            "confidence_indicator": skill_profile.get("problem_solving", 0),
            "hesitation_level": aggregate_metrics.get("idle_time_level", 0) if has_real_data else 0,
            # ===== BEHAVIORAL CONSISTENCY METRICS (NOT "anti-cheat") =====
            "focus_loss_count": sum(1 for e in event_list if e.get("event_type") == "focus_lost"),
            "paste_detected": any(e.get("event_type") == "paste_detected" for e in event_list),
            "paste_count": sum(1 for e in event_list if e.get("event_type") == "paste_detected"),
            "copy_detected": any(e.get("event_type") == "copy_detected" for e in event_list),
            "copy_count": sum(1 for e in event_list if e.get("event_type") == "copy_detected"),
            "long_idle_count": sum(1 for e in event_list if e.get("event_type") == "idle_detected"),
        },
        # NEW: Evidence-based explanations for each metric
        "metric_explanations": _generate_metric_explanations(
            aggregate_metrics, 
            behavioral_summary, 
            skill_profile,
            tasks_completed,
            total_tasks
        ) if has_real_data else {},
        "skill_profile": skill_profile,
        "behavioral_summary": behavioral_summary,
        "role_fit": role_fit,
        "resume_comparison": resume_comparison,
        # ===== OVERALL FIT SCORE with BEHAVIORAL CONSISTENCY ADJUSTMENT =====
        "overall_fit": _compute_overall_fit_score(
            per_task_metrics=per_task_metrics,
            aggregate_metrics=aggregate_metrics,
            skill_profile=skill_profile,
            resume_comparison=resume_comparison,
            behavioral_consistency_metrics={  # Renamed from anti_cheat_metrics
                "focus_loss_count": sum(1 for e in event_list if e.get("event_type") == "focus_lost"),
                "paste_count": sum(1 for e in event_list if e.get("event_type") == "paste_detected"),
                "copy_count": sum(1 for e in event_list if e.get("event_type") == "copy_detected"),
                "long_idle_count": sum(1 for e in event_list if e.get("event_type") == "idle_detected"),
            },
            total_tasks=total_tasks
        ) if has_real_data else {"score": 0, "grade": "—", "grade_label": "Not Started", "grade_color": "gray", "breakdown": {}},
        "candidate_insights": candidate_insights,
        "decision_path": decision_path,
        "chart_data": chart_data,
        "per_task_metrics": per_task_metrics,
        "aggregate_metrics": aggregate_metrics,
        "current_question": current_question,
        "computed_at": now.isoformat(),
        "ai_analysis": attempt.get("analysis_result"),
        # ===== POPULATION INTELLIGENCE (Black-box audit fixes) =====
        "population_intelligence": await _compute_population_intelligence(
            aggregate_metrics, skill_profile, per_task_metrics, tasks_completed, recruiter_id,
            anti_cheat_metrics={
                "focus_loss_count": sum(1 for e in event_list if e.get("event_type") == "focus_lost"),
                "paste_count": sum(1 for e in event_list if e.get("event_type") == "paste_detected"),
                "copy_count": sum(1 for e in event_list if e.get("event_type") == "copy_detected"),
                "long_idle_count": sum(1 for e in event_list if e.get("event_type") == "idle_detected"),
            }
        ) if has_real_data else None,
        # ===== FALSE POSITIVE PROTECTION =====
        "assessment_confidence": get_false_positive_protection().calculate_assessment_confidence(
            aggregate_metrics, per_task_metrics, 
            compute_behavioral_consistency(per_task_metrics, {
                "focus_loss_count": sum(1 for e in event_list if e.get("event_type") == "focus_lost"),
                "paste_count": sum(1 for e in event_list if e.get("event_type") == "paste_detected"),
                "copy_count": sum(1 for e in event_list if e.get("event_type") == "copy_detected"),
                "long_idle_count": sum(1 for e in event_list if e.get("event_type") == "idle_detected"),
            }) if has_real_data else {"flags": [], "confidence_explanation": {"level": "low"}},
            await _compute_population_intelligence(aggregate_metrics, skill_profile, per_task_metrics, tasks_completed, recruiter_id) if has_real_data else None
        ) if has_real_data else {"overall": 0, "level": "insufficient_data", "recommendation": {"action": "insufficient_data", "message": "No data available for confidence calculation"}},
        "override_controls": get_false_positive_protection().generate_override_controls(
            attempt_id, 
            _compute_overall_fit_score(per_task_metrics, aggregate_metrics, skill_profile, resume_comparison, {
                "focus_loss_count": sum(1 for e in event_list if e.get("event_type") == "focus_lost"),
                "paste_count": sum(1 for e in event_list if e.get("event_type") == "paste_detected"),
                "copy_count": sum(1 for e in event_list if e.get("event_type") == "copy_detected"),
                "long_idle_count": sum(1 for e in event_list if e.get("event_type") == "idle_detected"),
            }, total_tasks).get("grade", "—") if has_real_data else "—"
        ) if has_real_data and is_completed else None,
        "neurodiversity_considerations": get_false_positive_protection().check_neurodiversity_considerations(per_task_metrics) if has_real_data else {"considerations": []},
    }


async def get_attempt_answers(attempt_id: str) -> List[Dict]:
    """
    Gather all final answers for an attempt to send to AI analysis.
    """
    attempts_coll = get_attempts_collection()
    
    # Try finding attempt with ObjectId, fallback to string
    try:
        attempt = await attempts_coll.find_one({"_id": ObjectId(attempt_id)})
    except:
        attempt = None
        
    if not attempt:
        attempt = await attempts_coll.find_one({"_id": attempt_id})
        
    if not attempt:
        return []

    task_ids = attempt.get("task_ids", [])
    if not task_ids:
        return []

    events_coll = get_events_collection()
    
    # Robust event query handling both string and ObjectId attempt_id
    query = {
        "$or": [
            {"attempt_id": attempt_id},
            {"attempt_id": ObjectId(attempt_id)}
        ]
    }
    cursor = events_coll.find(query).sort("sequence_number", 1)
    events = await cursor.to_list(length=10000)

    # Fetch tasks metadata
    tasks_coll = get_tasks_collection()
    tasks_cursor = tasks_coll.find({"_id": {"$in": [ObjectId(tid) for tid in task_ids if ObjectId.is_valid(tid)]}})
    tasks_map = {str(task["_id"]): task async for task in tasks_cursor}

    answers = []
    
    for task_id in task_ids:
        # Filter for task events (robust matching)
        task_events = [e for e in events if str(e.get("task_id")) == str(task_id)]
        
        # Find the final task_completed event
        submission = next((e for e in reversed(task_events) if e.get("event_type") == "task_completed"), None)
        
        if not submission:
            continue
            
        task = tasks_map.get(str(task_id))
        if not task:
            continue

        payload = submission.get("payload", {})
        selected_opt_id = payload.get("selected_option_id")
        selected_text = "Unknown"
        is_correct = False
        
        # Resolve selected option text
        for opt in task.get("options", []):
            if opt["id"] == selected_opt_id:
                selected_text = opt["text"]
                is_correct = opt.get("risk_level") == "low"
                break
        
        # Extract reasoning - NO URL FILTER (allow urls for testing)
        reasoning = payload.get("reasoning", "")
        
        answers.append({
            "question_text": task.get("scenario", "") + " " + task.get("title", ""),
            "selected_option": selected_text,
            "reasoning_text": reasoning,
            "skills": attempt.get("candidate_info", {}).get("skills", []),
            "is_correct": is_correct
        })
    
    return answers




async def _get_current_question(attempt: Dict, events: List[Dict]) -> Optional[Dict]:
    """
    Get the current question details for the Recruiter Mirror View.
    Includes scenario, options, correct answer, and candidate's selection.
    """
    task_ids = attempt.get("task_ids", [])
    current_index = attempt.get("current_task_index", 0)
    
    if not task_ids or current_index >= len(task_ids):
        return None
    
    current_task_id = task_ids[current_index]
    
    # Fetch current task from database
    tasks_coll = get_tasks_collection()
    task = await tasks_coll.find_one({"_id": ObjectId(current_task_id)})
    
    if not task:
        return None
    
    # Build options array with correct answer marking
    options = []
    for opt in task.get("options", []):
        risk_level = opt.get("risk_level", "medium")
        options.append({
            "id": opt.get("id"),
            "text": opt.get("text"),
            "risk_level": risk_level,
            "is_correct": risk_level == "low",
        })
    
    # Find candidate's current selection from events
    candidate_selection = None
    reasoning_text = None
    focus_loss_count = 0
    paste_count = 0
    copy_count = 0
    
    # Filter events for current task and find latest option_selected/option_changed
    task_events = [e for e in events if e.get("task_id") == current_task_id]
    for event in reversed(task_events):
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        
        if event_type in ["option_selected", "option_changed"] and not candidate_selection:
            candidate_selection = payload.get("option_id")
        
        if event_type == "reasoning_updated" and not reasoning_text:
            reasoning_text = payload.get("reasoning_text", "")
            
        if event_type == "focus_lost":
            focus_loss_count += 1
        elif event_type == "paste_detected":
            paste_count += 1
        elif event_type == "copy_detected":
            copy_count += 1
    
    return {
        "task_id": current_task_id,
        "title": task.get("title", "Question"),
        "scenario": task.get("scenario", ""),
        "category": task.get("category", "problem_solving"),
        "difficulty": task.get("difficulty", "medium"),
        "options": options,
        "candidate_selection": candidate_selection,
        "reasoning_text": reasoning_text,
        "focus_loss_count": focus_loss_count,
        "paste_count": paste_count,
        "copy_count": copy_count,
    }

def _compute_resume_comparison(candidate_info: Dict, skill_profile: Dict, per_task_metrics: List[Dict] = None) -> Dict:
    """
    Compute observed skills based on actual assessment performance.
    
    Returns:
        Dict with:
            - observed_skills: List of { skill, score, trend }
            - overall_score: Average across all skills
    """
    resume_skills = candidate_info.get("skills", [])
    if not resume_skills:
        # Default skills to track if none provided
        resume_skills = ["Problem Solving", "Analytical Thinking", "Decision Making"]
    
    # Limit to 5 skills max for display
    resume_skills = resume_skills[:5]
    
    observed_skills = []
    total_score = 0
    
    # Map internal skill profile dimensions to external skills
    skill_mapping = {
        "problem solving": skill_profile.get("problem_solving", 0),
        "analytical": skill_profile.get("analytical_thinking", 0),
        "analytical thinking": skill_profile.get("analytical_thinking", 0),
        "decision": skill_profile.get("decision_speed", 0),
        "decision making": skill_profile.get("decision_speed", 0),
        "risk": skill_profile.get("risk_assessment", 0),
        "risk assessment": skill_profile.get("risk_assessment", 0),
        "creativity": skill_profile.get("creativity", 0),
    }
    
    for skill in resume_skills:
        skill_lower = skill.lower()
        
        # Try to find a matching internal dimension
        score = None
        for key, value in skill_mapping.items():
            if key in skill_lower or skill_lower in key:
                score = value
                break
        
        # If no match, use average of problem_solving and analytical
        if score is None:
            # No direct mapping found - use behavioral average as honest proxy
            # NO artificial variation - same input = same output
            base_score = (skill_profile.get("problem_solving", 0) + 
                         skill_profile.get("analytical_thinking", 0)) // 2
            score = base_score
        
        # Determine trend based on per-task improvement
        trend = "stable"
        if per_task_metrics and len(per_task_metrics) >= 2:
            # Compare first half vs second half metrics
            mid = len(per_task_metrics) // 2
            if mid > 0:
                first_half = per_task_metrics[:mid]
                second_half = per_task_metrics[mid:]
                
                # Use explanation detail as proxy for engagement trend (correctness not tracked)
                first_avg = sum(t.get("explanation_detail_score", t.get("word_count", 0)) for t in first_half) / len(first_half) if first_half else 0
                second_avg = sum(t.get("explanation_detail_score", t.get("word_count", 0)) for t in second_half) / len(second_half) if second_half else 0
                
                if second_avg > first_avg + 0.1:
                    trend = "improving"
                elif second_avg < first_avg - 0.1:
                    trend = "declining"
        
        observed_skills.append({
            "skill": skill,
            "score": int(score),
            "trend": trend
        })
        total_score += score
    
    overall_score = int(total_score / len(observed_skills)) if observed_skills else 0
    
    return {
        "observed_skills": observed_skills,
        "overall_score": overall_score,
        "skills_count": len(observed_skills),
        # Legacy fields for backward compatibility
        "skills_verified": sum(1 for s in observed_skills if s["score"] >= 70),
        "skills_total": len(observed_skills),
        "overall_match": overall_score,
        "claims": []  # Empty - no longer using claimed vs verified
    }


def _compute_role_fit(skill_profile: Dict, aggregate_metrics: Dict) -> Dict:
    """Compute overall role fit and recruiter metrics."""
    # Derived from skill profile
    ps = skill_profile.get("problem_solving", 0)
    ds = skill_profile.get("decision_speed", 0)
    at = skill_profile.get("analytical_thinking", 0)
    
    overall = int((ps * 0.4) + (at * 0.4) + (ds * 0.2))
    
    recommendation = "Strong Candidate" if overall >= 80 else "Follow-up Required" if overall >= 60 else "Low Match"
    
    return {
        "overall_score": overall,
        "recommendation": recommendation,
        "confidence": "High" if ps > 70 else "Moderate",
        "technical_fit": int(ps),
        "cultural_fit": int((at + skill_profile.get("risk_assessment", 0)) / 2),
        "experience_fit": int((ps + at) / 2),
    }


def _compute_overall_fit_score(
    per_task_metrics: List[Dict],
    aggregate_metrics: Dict,
    skill_profile: Dict,
    resume_comparison: Dict,
    behavioral_consistency_metrics: Dict,  # Renamed from anti_cheat_metrics
    total_tasks: int
) -> Dict:
    """
    Compute the Overall Fit Score with transparent formula breakdown.
    
    Formula: FitScore = (Task×0.30) + (Behavioral×0.35) + (Skill×0.25) + (Resume×0.10) - AntiCheatPenalty
    
    Returns:
        Dict with score, grade, breakdown, and explanation
    """
    # ======== 1. TASK SCORE (30%) ========
    # Completion rate + Accuracy (correctness)
    completed_tasks = [t for t in per_task_metrics if t.get("is_completed", False)]
    tasks_completed = len(completed_tasks)
    
    if total_tasks > 0:
        completion_rate = (tasks_completed / total_tasks) * 100
    else:
        completion_rate = 0
    
    # Accuracy: % of correct answers among completed tasks
    correct_answers = sum(1 for t in completed_tasks if t.get("is_correct", False))
    if tasks_completed > 0:
        accuracy_rate = (correct_answers / tasks_completed) * 100
    else:
        accuracy_rate = 0
    
    task_score = (completion_rate * 0.4) + (accuracy_rate * 0.6)
    task_score = min(100, max(0, task_score))  # Clamp 0-100
    
    # ======== SKIP PENALTY ========
    # Each skipped question applies a direct penalty to the behavioral score
    skipped_count = sum(1 for t in per_task_metrics if t.get("is_skipped", False))
    skip_penalty = skipped_count * 5  # -5 points per skip
    
    # ======== 2. BEHAVIORAL SCORE (35%) ========
    # Decision firmness + Session continuity + Response quality
    decision_firmness = aggregate_metrics.get("decision_firmness", 0) or 0
    
    # Session continuity from aggregate
    total_changes = aggregate_metrics.get("total_changes", 0)
    session_continuity = max(0, 100 - min(100, total_changes * 15))
    
    # Response quality: inverse of idle time level
    idle_time_level = aggregate_metrics.get("idle_time_level", 0) or 0
    response_quality = 100 - min(100, idle_time_level)
    
    behavioral_score = (decision_firmness * 0.4) + (session_continuity * 0.3) + (response_quality * 0.3)
    behavioral_score = min(100, max(0, behavioral_score - skip_penalty))  # Apply skip penalty
    
    # ======== 3. SKILL SCORE (25%) ========
    # Average of 5 skill dimensions
    ps = skill_profile.get("problem_solving", 0) or 0
    at = skill_profile.get("analytical_thinking", 0) or 0
    ds = skill_profile.get("decision_speed", 0) or 0
    cr = skill_profile.get("creativity", 0) or 0
    ra = skill_profile.get("risk_assessment", 0) or 0
    
    skill_score = (ps + at + ds + cr + ra) / 5
    skill_score = min(100, max(0, skill_score))
    
    # ======== 4. RESUME ALIGNMENT (10%) ========
    # How well observed skills match claimed skills
    resume_alignment = resume_comparison.get("overall_score", 0) or 0
    resume_alignment = min(100, max(0, resume_alignment))
    
    # ======== 5. BEHAVIORAL CONSISTENCY ADJUSTMENT (up to -10 points, reduced from -15) ========
    focus_loss_count = behavioral_consistency_metrics.get("focus_loss_count", 0) or 0
    paste_count = behavioral_consistency_metrics.get("paste_count", 0) or 0
    copy_count = behavioral_consistency_metrics.get("copy_count", 0) or 0
    long_idle_count = behavioral_consistency_metrics.get("long_idle_count", 0) or 0
    
    penalty = 0
    penalty += min(3, focus_loss_count * 0.5)  # -0.5 per tab switch, max -3 (reduced)
    penalty += min(3, paste_count * 1.5)       # -1.5 per paste, max -3 (reduced)
    penalty += min(2, copy_count * 2)          # -2 per copy, max -2 (reduced)
    penalty += min(2, long_idle_count * 0.5)   # -0.5 per long idle, max -2
    consistency_adjustment = min(10, penalty)  # Renamed from anti_cheat_penalty, max -10 (reduced from -15)
    
    adjustment_reasons = []
    if focus_loss_count > 0:
        adjustment_reasons.append(f"{focus_loss_count} window navigation event(s)")
    if paste_count > 0:
        adjustment_reasons.append(f"{paste_count} rapid text entry event(s)")
    if copy_count > 0:
        adjustment_reasons.append(f"{copy_count} content copy event(s)")
    if long_idle_count > 0:
        adjustment_reasons.append(f"{long_idle_count} extended pause(s)")
    
    # ======== FINAL SCORE CALCULATION ========
    weighted_task = task_score * 0.30
    weighted_behavioral = behavioral_score * 0.35
    weighted_skill = skill_score * 0.25
    weighted_resume = resume_alignment * 0.10
    
    raw_score = weighted_task + weighted_behavioral + weighted_skill + weighted_resume
    final_score = max(0, round(raw_score - consistency_adjustment))  # Renamed from anti_cheat_penalty
    
    # Determine grade
    if final_score >= 90:
        grade = "S"
        grade_label = "Exceptional Match"
        grade_color = "gold"
    elif final_score >= 80:
        grade = "A"
        grade_label = "Strong Match"
        grade_color = "green"
    elif final_score >= 70:
        grade = "B"
        grade_label = "Good Match"
        grade_color = "blue"
    elif final_score >= 60:
        grade = "C"
        grade_label = "Moderate Match"
        grade_color = "yellow"
    else:
        grade = "D"
        grade_label = "Low Match"
        grade_color = "red"
    
    return {
        "score": final_score,
        "grade": grade,
        "grade_label": grade_label,
        "grade_color": grade_color,
        "breakdown": {
            "task_score": {
                "raw": round(task_score, 1),
                "weight": 0.30,
                "contribution": round(weighted_task, 1),
                "details": {
                    "completion_rate": round(completion_rate, 1),
                    "accuracy_rate": round(accuracy_rate, 1),
                    "tasks_completed": tasks_completed,
                    "correct_answers": correct_answers,
                    "total_tasks": total_tasks
                }
            },
            "behavioral_score": {
                "raw": round(behavioral_score, 1),
                "weight": 0.35,
                "contribution": round(weighted_behavioral, 1),
                "details": {
                    "decision_firmness": round(decision_firmness, 1),
                    "session_continuity": round(session_continuity, 1),
                    "response_quality": round(response_quality, 1)
                }
            },
            "skill_score": {
                "raw": round(skill_score, 1),
                "weight": 0.25,
                "contribution": round(weighted_skill, 1),
                "details": {
                    "problem_solving": ps,
                    "analytical_thinking": at,
                    "decision_speed": ds,
                    "creativity": cr,
                    "risk_assessment": ra
                }
            },
            "resume_alignment": {
                "raw": round(resume_alignment, 1),
                "weight": 0.10,
                "contribution": round(weighted_resume, 1)
            },
            "behavioral_consistency_adjustment": {  # Renamed from anti_cheat_penalty
                "value": -round(consistency_adjustment, 1),
                "reasons": adjustment_reasons,
                "details": {
                    "focus_loss_count": focus_loss_count,
                    "paste_count": paste_count,
                    "copy_count": copy_count,
                    "long_idle_count": long_idle_count
                }
            }
        },
        "formula": "(Task×0.30) + (Behavioral×0.35) + (Skill×0.25) + (Resume×0.10) - ConsistencyAdjustment",
        "explanation": f"Score of {final_score} reflects {grade_label.lower()} based on {tasks_completed}/{total_tasks} tasks completed with {correct_answers} correct answers." + 
                       (f" Behavioral consistency adjustment of {consistency_adjustment} applied for: {', '.join(adjustment_reasons)}." if adjustment_reasons else "")
    }


# ============================================================================
# PER-TASK METRICS
# ============================================================================
async def _compute_per_task_metrics(events: List[Dict], task_ids: List[str], assessment_started_at=None) -> List[Dict]:
    """Compute metrics for each task from logged events.
    
    assessment_started_at: Optional fallback start time for the first task
                          when TASK_STARTED event is missing (WebSocket timing issue).
    """
    
    # Fetch task content to provide context
    tasks_coll = get_tasks_collection()
    tasks_cursor = tasks_coll.find({"_id": {"$in": [ObjectId(tid) for tid in task_ids]}}) # Changed to _id
    tasks_content = {str(t["_id"]): t async for t in tasks_cursor} # Changed to _id
    
    # Group events by task
    task_events = {}
    for event in events:
        task_id = event["task_id"]
        if task_id not in task_events:
            task_events[task_id] = []
        task_events[task_id].append(event)
    
    per_task = []
    
    for task_id in task_ids:
        # Get task content if available
        task_data = tasks_content.get(task_id, {})
        
        if task_id not in task_events:
            # If no events yet, return basic structure
            per_task.append({
                "task_id": task_id,
                "scenario": task_data.get("scenario", ""),
                "difficulty": task_data.get("difficulty", "medium"),
                "is_completed": False
            })
            continue
        
        events_for_task = task_events[task_id]
        
        # Find key events
        task_started = None
        task_completed = None
        first_selection = None
        final_selection_index = None
        option_changes = 0
        options_viewed = set()
        reasoning_text = ""
        is_skipped = False
        focus_loss_count = 0  # Per-question anti-cheat
        paste_detected = False  # Per-question anti-cheat
        paste_count = 0  # Per-question anti-cheat
        copy_detected = False  # Per-question anti-cheat
        copy_count = 0  # Per-question anti-cheat
        idle_event_count = 0  # Per-question anti-cheat
        
        for event in events_for_task:
            event_type = event["event_type"]
            
            if event_type == EventType.TASK_STARTED.value:
                task_started = event
            elif event_type == EventType.TASK_COMPLETED.value:
                task_completed = event
                final_selection_index = event.get("payload", {}).get("selected_option_index")
                # Get final reasoning if available
                reasoning_text = event.get("payload", {}).get("reasoning", "")
            elif event_type == EventType.TASK_SKIPPED.value:
                is_skipped = True
                task_completed = event  # Treat skip as completion for time tracking
            elif event_type == EventType.OPTION_SELECTED.value:
                if first_selection is None:
                    first_selection = event
                option_id = event.get("payload", {}).get("option_index")
                if option_id is not None:
                    options_viewed.add(option_id)
            elif event_type == EventType.OPTION_CHANGED.value:
                option_changes += 1
            # Per-question anti-cheat metrics
            elif event_type == "focus_lost":
                focus_loss_count += 1
            elif event_type == "paste_detected":
                paste_detected = True
                paste_count += 1
            elif event_type == "copy_detected":
                copy_detected = True
                copy_count += 1
            elif event_type == "idle_detected":
                idle_event_count += 1
        
        # Calculate time metrics
        now = datetime.utcnow()
        
        # For first task, use assessment_started_at as fallback if no TASK_STARTED event
        if not task_started and task_ids.index(task_id) == 0 and assessment_started_at:
            start_time = assessment_started_at
        elif task_started:
            start_time = task_started["timestamp"]
        else:
            start_time = None
        
        if start_time:
            if task_completed:
                time_spent = (task_completed["timestamp"] - start_time).total_seconds()
            else:
                time_spent = (now - start_time).total_seconds()
        else:
            time_spent = 0.0
        
        if start_time and first_selection:
            first_decision_speed = (first_selection["timestamp"] - start_time).total_seconds()
            hesitation = first_decision_speed
        else:
            first_decision_speed = time_spent
            hesitation = time_spent
        
        # Compute explanation metrics
        word_count = len(reasoning_text.split()) if reasoning_text else 0
        connector_count = sum(1 for kw in LOGICAL_KEYWORDS if kw in reasoning_text.lower())
        connector_ratio = connector_count / max(word_count / 20, 1) if word_count > 0 else 0
        explanation_detail_score = min(1.0, word_count / THRESHOLDS["detailed_explanation"]) * 0.6 + min(1.0, connector_ratio) * 0.4
        explanation_detail_normalized = round(explanation_detail_score * 100, 2)
        
        # --- DERIVED BEHAVIORAL METRICS FOR HISTORY VIEW ---
        
        # Selection Speed Label
        if first_decision_speed < THRESHOLDS["fast_decision"]:
            speed_label = "Quick"
        elif first_decision_speed > THRESHOLDS["slow_decision"]:
            speed_label = "Extended"
        else:
            speed_label = "Moderate"
            
        # Session Continuity (per question)
        # Penalize for high changes or high idle ratio
        idle_time_ratio = hesitation / max(time_spent, 1)
        continuity_score = max(0, 100 - (option_changes * 10) - int(idle_time_ratio * 40))
        
        # Observed Pattern
        if option_changes == 0 and speed_label == "Quick":
            pattern = "Direct"
        elif option_changes > 2:
            pattern = "Iterative"
        elif speed_label == "Extended":
            pattern = "Deliberative"
        else:
            pattern = "Balanced"
            
        # Recruiter Summary / Flag
        summary = "Standard completed"
        summary_score = 100
        if continuity_score < 60:
            summary = "Frequent revisions observed"
            summary_score = continuity_score
        elif option_changes > 4:
            summary = "Multiple revisions before final selection"
            summary_score = 70
        elif word_count < 10 and task_completed:
            summary = "Concise explanation provided"
            summary_score = 80
             
        # Format options with candidate selection
        options_data = task_data.get("options", [])
        final_options = []
        correct_option_id = None
        for i, opt in enumerate(options_data):
            opt_id = i  # Assuming 0-indexed options
            is_selected = (final_selection_index == opt_id)
            # Find correct option (usually stored as 'is_correct' or we check metadata)
            # For now assuming 'is_correct' might be in option or we skip if not available
            # If options are simple strings, we might need to adjust. Assuming dicts from seed.
            if isinstance(opt, dict):
                 is_correct = opt.get("risk_level") == "low" # Changed to risk_level
                 if is_correct: correct_option_id = opt_id
                 final_options.append({
                     "id": opt_id,
                     "text": opt.get("text", ""),
                     "is_selected": is_selected,
                     "is_correct": is_correct
                 })
            else:
                # String options fallback
                final_options.append({
                    "id": opt_id,
                    "text": str(opt),
                    "is_selected": is_selected,
                    "is_correct": False
                })

        per_task.append({
            "task_id": task_id,
            "scenario": task_data.get("scenario", ""),
            "difficulty": task_data.get("difficulty", "medium"),
            "options": final_options,
            "correct_option_id": correct_option_id,
            "candidate_selection_id": final_selection_index,
            
            # Metrics
            "time_spent_seconds": round(time_spent, 2),
            "idle_time_seconds": round(hesitation, 2),
            "initial_selection_seconds": round(first_decision_speed, 2),
            "selection_speed_label": speed_label,  # Quick/Moderate/Extended
            "decision_changes": option_changes,
            "session_continuity_score": continuity_score,
            
            "explanation_word_count": word_count,
            "explanation_detail_score": explanation_detail_score,
            "reasoning_depth": explanation_detail_normalized,
            "observed_pattern": pattern,
            "recruiter_summary": summary,
            "recruiter_score": summary_score,
            
            "is_completed": task_completed is not None,
            "is_correct": False if is_skipped else (correct_option_id is not None and correct_option_id == final_selection_index),
            "is_skipped": is_skipped,
            
            # Per-question anti-cheat metrics (Phase 10)
            "focus_loss_count": focus_loss_count,
            "paste_detected": paste_detected,
            "paste_count": paste_count,
            "copy_detected": copy_detected,
            "copy_count": copy_count,
            "idle_event_count": idle_event_count,
        })
    
    return per_task


def _compute_aggregate_metrics(per_task_metrics: List[Dict], total_time: float) -> Dict:
    """Compute aggregate metrics from per-task data. Uses behavioral terminology."""
    if not per_task_metrics:
        return {
            "total_time_seconds": total_time,
            "total_changes": 0,
            "avg_initial_selection": 0,  # renamed from avg_decision_speed
            "avg_idle_time": 0,  # renamed from avg_hesitation
            "selection_speed_label": "N/A",  # renamed from hesitation_label
            "idle_time_level": 0,  # renamed from hesitation_level
            "total_explanation_words": 0,
            "reasoning_depth": 0,
            "cheating_resilience": 100,  # default to perfect score
            "tasks_completed": 0,
        }
    
    total_changes = sum(m.get("decision_changes", 0) for m in per_task_metrics)
    total_idle = sum(m.get("idle_time_seconds", 0) for m in per_task_metrics)
    selection_times = [m.get("initial_selection_seconds", 0) for m in per_task_metrics]
    explanation_details = [m.get("explanation_detail_score", 0) for m in per_task_metrics]
    total_explanation_words = sum(m.get("explanation_word_count", 0) for m in per_task_metrics)
    tasks_completed = sum(1 for m in per_task_metrics if m.get("is_completed", False))
    
    avg_initial_selection = sum(selection_times) / len(selection_times) if selection_times else 0
    avg_idle_time = total_idle / len(per_task_metrics)
    reasoning_depth = sum(explanation_details) / len(explanation_details) if explanation_details else 0
    
    # NEW: Cheating Resilience Calculation (Audit Layer 5 integration)
    total_focus_loss = sum(m.get("focus_loss_count", 0) for m in per_task_metrics)
    total_pastes = sum(m.get("paste_count", 0) for m in per_task_metrics)
    total_copies = sum(m.get("copy_count", 0) for m in per_task_metrics)
    cheating_resilience = max(0, 100 - (total_focus_loss * 10) - (total_pastes * 20) - (total_copies * 5))
    
    # Determine selection speed label (RELATIVE context, not absolute judgment)
    # Audit fix: Show relative speed ("Faster than 73% of candidates") not just absolute labels
    if avg_initial_selection < THRESHOLDS["fast_decision"]:
        selection_speed_label = "Quick"
    elif avg_initial_selection < THRESHOLDS["slow_decision"]:
        selection_speed_label = "Moderate"
    else:
        selection_speed_label = "Extended"
    
    # NEW: Relative speed context (audit requirement - Layer 1)
    # This provides population-relative context instead of absolute labels
    speed_context = {
        "absolute_seconds": round(avg_initial_selection, 1),
        "label": selection_speed_label,
        "context_note": (
            f"Average first-click time of {avg_initial_selection:.1f}s. "
            f"Thresholds: Quick < {THRESHOLDS['fast_decision']}s, "
            f"Moderate {THRESHOLDS['fast_decision']}-{THRESHOLDS['slow_decision']}s, "
            f"Extended > {THRESHOLDS['slow_decision']}s."
        ),
        "interpretation_note": (
            "Speed varies by question familiarity, anxiety, and language proficiency. "
            "Use as one signal among many, not as a standalone judgment."
        ),
    }
    
    # Idle time: return actual seconds AND categorical label
    if avg_idle_time < 5:
        idle_time_label = "Low"
    elif avg_idle_time < 15:
        idle_time_label = "Moderate"
    else:
        idle_time_label = "High"
    
    return {
        "total_time_seconds": total_time,
        "total_changes": total_changes,
        "avg_initial_selection": round(avg_initial_selection, 2),
        "avg_idle_time": round(avg_idle_time, 2),
        "selection_speed_label": selection_speed_label,
        "speed_context": speed_context,  # NEW: Relative speed context (audit Layer 1)
        "idle_time_level": round(avg_idle_time, 1),  # CHANGED: actual seconds, not % bucket
        "idle_time_label": idle_time_label,  # NEW: categorical label
        "total_explanation_words": total_explanation_words,
        "reasoning_depth": round(reasoning_depth * 100, 2),
        "cheating_resilience": int(cheating_resilience),
        "tasks_completed": tasks_completed,
        "focus_loss_count": total_focus_loss,
        "paste_count": total_pastes,
        "copy_count": total_copies,
        "paste_detected": total_pastes > 0,
        "copy_detected": total_copies > 0,
    }


# ============================================================================
# SKILL PROFILE (RADAR CHART) - Behavioral Observations with Evidence
# ============================================================================
def _compute_skill_profile(aggregate_metrics: Dict, per_task_metrics: List[Dict]) -> Dict:
    """
    Compute skill profile for radar chart.
    Returns scores 0-100 for each dimension.
    Labels describe observable patterns, not psychological traits.
    """
    if not per_task_metrics:
        return {
            "task_completion": 0,  # renamed from problem_solving
            "selection_speed": 0,  # renamed from decision_speed
            "deliberation_pattern": 0,  # renamed from analytical_thinking
            "option_exploration": 0,  # renamed from creativity
            "risk_preference": 0,  # renamed from risk_assessment
        }
    
    avg_initial_selection = aggregate_metrics.get("avg_initial_selection", 30)
    total_changes = aggregate_metrics.get("total_changes", 0)
    reasoning_depth = aggregate_metrics.get("reasoning_depth", 0)
    tasks_completed = aggregate_metrics.get("tasks_completed", 0)
    total_tasks = len(per_task_metrics)
    
    # Task Completion Score (renamed from problem_solving - observable completion)
    completion_rate = tasks_completed / total_tasks if total_tasks > 0 else 0
    task_completion = int(min(100, (completion_rate * 60) + (reasoning_depth / 2)))
    
    # Selection Speed Score (renamed from decision_speed - describes timing pattern)
    if avg_initial_selection < THRESHOLDS["fast_decision"]:
        selection_speed_score = 90 + (10 * (1 - avg_initial_selection / THRESHOLDS["fast_decision"]))
    elif avg_initial_selection < THRESHOLDS["slow_decision"]:
        # Between fast and slow
        ratio = (avg_initial_selection - THRESHOLDS["fast_decision"]) / (THRESHOLDS["slow_decision"] - THRESHOLDS["fast_decision"])
        selection_speed_score = 90 - (ratio * 40)
    else:
        # Extended selection time
        selection_speed_score = max(20, 50 - (avg_initial_selection - THRESHOLDS["slow_decision"]))
    
    # Deliberation Pattern Score (renamed from analytical_thinking - describes time + detail)
    deliberation_pattern = int(min(100, reasoning_depth + (completion_rate * 30)))
    
    # Option Exploration Score - GATED: only count real exploration data
    # Currently we track selection changes, not option views
    # Each revision suggests exploring alternatives - honest proxy
    if total_changes == 0:
        option_exploration = 0  # No exploration observed yet
    else:
        # Cap at reasonable max (8 revisions = 96, practically 100)
        option_exploration = int(min(100, min(total_changes, 8) * 12))
    
    # Risk Preference Score (renamed from risk_assessment - describes choice patterns)
    avg_idle_time = aggregate_metrics.get("avg_idle_time", 0)
    if avg_idle_time > 5:  # Some deliberation before choices
        risk_preference = int(min(100, 50 + avg_idle_time * 5))
    else:
        risk_preference = int(max(30, avg_idle_time * 10))
    
    # Build drill-down evidence for each radar axis (audit Layer 3 requirement)
    evidence = {
        "task_completion": {
            "score": min(100, max(0, task_completion)),
            "raw_data": {
                "tasks_completed": tasks_completed,
                "total_tasks": total_tasks,
                "completion_rate": round(completion_rate * 100, 1),
                "reasoning_depth": round(reasoning_depth, 1),
            },
            "formula": f"min(100, (completion_rate × 60) + (reasoning_depth / 2)) = min(100, ({completion_rate:.2f} × 60) + ({reasoning_depth:.1f} / 2)) = {task_completion}",
            "contributing_events": [
                f"Completed {tasks_completed}/{total_tasks} tasks",
                f"Average reasoning depth: {reasoning_depth:.1f}%",
            ],
        },
        "selection_speed": {
            "score": min(100, max(0, int(selection_speed_score))),
            "raw_data": {
                "avg_first_click_seconds": round(avg_initial_selection, 1),
                "threshold_fast": THRESHOLDS["fast_decision"],
                "threshold_slow": THRESHOLDS["slow_decision"],
            },
            "formula": f"Based on avg first-click time of {avg_initial_selection:.1f}s against thresholds",
            "contributing_events": [
                f"Average first click: {avg_initial_selection:.1f}s",
                f"Classification: {'Quick' if avg_initial_selection < THRESHOLDS['fast_decision'] else 'Extended' if avg_initial_selection > THRESHOLDS['slow_decision'] else 'Moderate'}",
            ],
        },
        "deliberation_pattern": {
            "score": min(100, max(0, deliberation_pattern)),
            "raw_data": {
                "reasoning_depth": round(reasoning_depth, 1),
                "completion_rate": round(completion_rate * 100, 1),
            },
            "formula": f"min(100, reasoning_depth + (completion_rate × 30)) = min(100, {reasoning_depth:.1f} + ({completion_rate:.2f} × 30)) = {deliberation_pattern}",
            "contributing_events": [
                f"Reasoning depth: {reasoning_depth:.1f}%",
                f"Completion contribution: {completion_rate * 30:.1f}",
            ],
        },
        "option_exploration": {
            "score": min(100, max(0, option_exploration)),
            "raw_data": {
                "total_option_changes": total_changes,
                "avg_changes_per_task": round(total_changes / total_tasks, 1) if total_tasks > 0 else 0,
            },
            "formula": f"min(100, min(total_changes, 8) × 12) = min(100, min({total_changes}, 8) × 12) = {option_exploration}",
            "contributing_events": [
                f"Total option changes: {total_changes}",
                f"Average per task: {total_changes / total_tasks:.1f}" if total_tasks > 0 else "No tasks",
            ],
        },
        "risk_preference": {
            "score": min(100, max(0, risk_preference)),
            "raw_data": {
                "avg_idle_time_seconds": round(avg_idle_time, 1),
            },
            "formula": f"Based on avg idle time of {avg_idle_time:.1f}s",
            "contributing_events": [
                f"Average idle time: {avg_idle_time:.1f}s",
                f"Deliberation level: {'Some' if avg_idle_time > 5 else 'Minimal'}",
            ],
        },
    }
    
    return {
        "task_completion": min(100, max(0, task_completion)),
        "selection_speed": min(100, max(0, int(selection_speed_score))),
        "deliberation_pattern": min(100, max(0, deliberation_pattern)),
        "option_exploration": min(100, max(0, option_exploration)),
        "risk_preference": min(100, max(0, risk_preference)),
        # Also return legacy keys for backward compatibility
        "problem_solving": min(100, max(0, task_completion)),
        "decision_speed": min(100, max(0, int(selection_speed_score))),
        "analytical_thinking": min(100, max(0, deliberation_pattern)),
        "creativity": min(100, max(0, option_exploration)),
        "risk_assessment": min(100, max(0, risk_preference)),
        # NEW: Drill-down evidence for each radar axis (audit Layer 3)
        "evidence": evidence,
    }


# ============================================================================
# BEHAVIORAL SUMMARY - Progressive Analysis with Confidence
# ============================================================================
# Minimum questions needed for confident pattern detection
MIN_QUESTIONS_FOR_PATTERN = 2
MIN_QUESTIONS_FOR_CONFIDENCE = 3

def _compute_behavioral_summary(aggregate_metrics: Dict, per_task_metrics: List[Dict] = None) -> Dict:
    """
    Compute behavioral summary using PROGRESSIVE pattern analysis.
    
    Key principles:
    1. Don't conclude from a single question - behavior emerges over time
    2. Track pattern distribution across all completed questions
    3. Show confidence that grows with more data
    4. Identify dominant pattern vs secondary patterns
    """
    # Get completed tasks only
    completed_tasks = [t for t in (per_task_metrics or []) if t.get("is_completed")]
    num_completed = len(completed_tasks)
    
    # If no completed tasks, return waiting state
    if num_completed == 0:
        return {
            "approach_pattern": None,
            "decision_style": None,
            "behavioral_mode": None,
            "approach": None,
            "pressure_pattern": None,
            "under_pressure": None,
            "verdict": None,
            "change_rate": None,
            "strength": None,
            "improvement_area": None,
            "all_strengths": [],
            "all_improvements": [],
            "confidence_level": 0,
            "pattern_distribution": {},
            "analysis_status": "waiting",
        }
    
    # Count pattern occurrences from each completed question
    pattern_counts = {"Direct": 0, "Iterative": 0, "Deliberative": 0, "Balanced": 0}
    speed_counts = {"Quick": 0, "Moderate": 0, "Extended": 0}
    
    for task in completed_tasks:
        pattern = task.get("observed_pattern", "Balanced")
        speed = task.get("selection_speed_label", "Moderate")
        
        if pattern in pattern_counts:
            pattern_counts[pattern] += 1
        if speed in speed_counts:
            speed_counts[speed] += 1
    
    # Calculate pattern distribution percentages
    pattern_distribution = {k: round((v / num_completed) * 100) for k, v in pattern_counts.items() if v > 0}
    
    # Find dominant pattern (most frequent)
    dominant_pattern = max(pattern_counts, key=pattern_counts.get)
    dominant_count = pattern_counts[dominant_pattern]
    dominant_percentage = round((dominant_count / num_completed) * 100)
    
    # Calculate confidence level (grows with more questions)
    # 1 question = 25%, 2 = 50%, 3 = 75%, 4+ = scales toward 95%
    if num_completed == 1:
        confidence_level = 25
        analysis_status = "preliminary"
    elif num_completed == 2:
        confidence_level = 50
        analysis_status = "developing"
    elif num_completed == 3:
        confidence_level = 75
        analysis_status = "confident"
    else:
        # Cap at 95% - never 100% certainty
        confidence_level = min(95, 75 + (num_completed - 3) * 5)
        analysis_status = "high_confidence"
    
    # Boost confidence if pattern is consistent (same pattern > 60% of time)
    if dominant_percentage >= 70:
        confidence_level = min(95, confidence_level + 10)
    
    # Determine if we have enough data for definitive labels
    if num_completed < MIN_QUESTIONS_FOR_PATTERN:
        # Show tentative pattern with clear uncertainty
        approach_pattern = f"{dominant_pattern}*"  # asterisk indicates preliminary
        behavioral_mode = f"Analyzing ({num_completed}/{MIN_QUESTIONS_FOR_PATTERN})"
    else:
        approach_pattern = dominant_pattern
        # Map pattern to behavioral mode
        mode_map = {
            "Deliberative": "Detail-oriented",
            "Direct": "Efficiency-focused", 
            "Iterative": "Exploration-focused",
            "Balanced": "Adaptive"
        }
        behavioral_mode = mode_map.get(dominant_pattern, "Adaptive")
    
    # Change rate from aggregate
    total_changes = aggregate_metrics.get("total_changes", 0)
    avg_changes_per_task = total_changes / num_completed if num_completed > 0 else 0
    
    if avg_changes_per_task <= 1:
        change_rate = "Low"
    elif avg_changes_per_task >= 3:
        change_rate = "High"
    else:
        change_rate = "Moderate"
    
    # Pacing Analysis (renamed from "Under Pressure" - audit Layer 7)
    # This is now framed as "behavioral shift observation" not "stress response"
    # It informs, not disqualifies. Framed as pacing change, not weakness.
    avg_idle_time = aggregate_metrics.get("avg_idle_time", 0)
    
    if num_completed < MIN_QUESTIONS_FOR_PATTERN:
        pressure_pattern = f"Observing... ({num_completed}q)"
        pacing_context = "Insufficient data for pacing analysis"
    elif avg_idle_time > 15 and total_changes > 3:
        pressure_pattern = "Variable pacing"
        pacing_context = (
            "Pacing varied across questions. Possible interpretations: "
            "candidate found some questions more challenging, "
            "candidate was warming up to the format, "
            "or candidate was managing time strategically."
        )
    elif total_changes / num_completed > 3:
        pressure_pattern = "Frequent revisions"
        pacing_context = (
            "Multiple revisions observed. This may indicate thorough exploration, "
            "uncertainty, or a preference for iterative decision-making."
        )
    elif dominant_pattern == "Direct":
        pressure_pattern = "Steady progression"
        pacing_context = "Consistent pacing throughout. Candidate maintained a steady approach."
    else:
        pressure_pattern = "Consistent approach"
        pacing_context = "Pacing was generally consistent across questions."
    
    # Strengths and improvements - only show after MIN_QUESTIONS
    strengths = []
    improvements = []
    
    if num_completed >= MIN_QUESTIONS_FOR_PATTERN:
        avg_explanation = aggregate_metrics.get("reasoning_depth", 0)
        avg_selection = aggregate_metrics.get("avg_initial_selection", 0)
        
        if avg_explanation > 30:
            strengths.append("Consistently detailed explanations")
        if avg_selection < THRESHOLDS["fast_decision"]:
            strengths.append("Quick decision-making pattern")
        if dominant_percentage >= 70:
            strengths.append(f"Consistent {dominant_pattern.lower()} approach")
        if avg_changes_per_task <= 1:
            strengths.append("Maintains initial selections")
            
        if avg_explanation < 20:
            improvements.append("Brief explanations observed")
        if avg_selection > THRESHOLDS["slow_decision"]:
            improvements.append("Extended deliberation times")
        if avg_changes_per_task > 3:
            improvements.append("Frequent answer revisions")
    
    if not strengths:
        strengths = ["Completing assessment systematically"]
    if not improvements:
        improvements = ["No specific concerns"]
    
    # NEW: Correctness Rate - percentage of correctly answered questions
    correct_count = sum(1 for task in completed_tasks if task.get("is_correct", False))
    correctness_rate = round((correct_count / num_completed) * 100) if num_completed > 0 else 0
    
    return {
        "approach_pattern": approach_pattern,
        "decision_style": approach_pattern,  # backward compatibility
        "behavioral_mode": behavioral_mode,
        "approach": behavioral_mode,  # backward compatibility
        "pressure_pattern": pressure_pattern,
        "under_pressure": pressure_pattern,  # backward compatibility
        "pacing_context": pacing_context,  # NEW: Contextual interpretation (audit Layer 7)
        "pacing_is_informational": True,  # NEW: Flag that this is informational, not evaluative
        "verdict": None,  # AI fills this after completion
        "change_rate": change_rate,
        "strength": strengths[0],
        "observed_strength": strengths[0],
        "improvement_area": improvements[0],
        "area_for_consideration": improvements[0],
        "all_strengths": strengths,
        "all_improvements": improvements,
        # NEW: Progressive analysis fields
        "confidence_level": confidence_level,
        "pattern_distribution": pattern_distribution,
        "dominant_pattern": dominant_pattern,
        "dominant_percentage": dominant_percentage,
        "questions_analyzed": num_completed,
        "analysis_status": analysis_status,
        "correctness_rate": correctness_rate,  # NEW: Performance metric
        "correct_count": correct_count,  # NEW: Raw count
    }


# ============================================================================
# RECRUITER VIEW
# ============================================================================
def _compute_recruiter_view(skill_profile: Dict, behavioral_summary: Dict) -> Dict:
    """
    Compute recruiter-specific view metrics.
    """
    # Role Fit Score (weighted average of skill dimensions)
    weights = {
        "problem_solving": 0.25,
        "decision_speed": 0.20,
        "analytical_thinking": 0.25,
        "creativity": 0.15,
        "risk_assessment": 0.15,
    }
    
    role_fit_score = sum(
        skill_profile.get(skill, 0) * weight 
        for skill, weight in weights.items()
    )
    
    # Logical Match (based on analytical thinking and reasoning)
    analytical = skill_profile.get("analytical_thinking", 0)
    if analytical >= 70:
        logical_match = "High"
    elif analytical >= 40:
        logical_match = "Moderate"
    else:
        logical_match = "Low"
    
    # Innovative Match (based on creativity and exploration)
    creativity = skill_profile.get("creativity", 0)
    if creativity >= 70:
        innovative_match = "High"
    elif creativity >= 40:
        innovative_match = "Moderate"
    else:
        innovative_match = "Low"
    
    return {
        "role_fit_score": int(role_fit_score),
        "logical_match": logical_match,
        "innovative_match": innovative_match,
    }


# ============================================================================
# CANDIDATE INSIGHTS - Behavioral Observations with Uncertainty Language
# ============================================================================
def _compute_candidate_insights(behavioral_summary: Dict, aggregate_metrics: Dict) -> List[Dict]:
    """
    Generate candidate insights using behavioral descriptions.
    Uses uncertainty language ("suggests", "observed", "may indicate").
    """
    insights = []
    
    approach_pattern = behavioral_summary.get("approach_pattern", "")
    reasoning_depth = aggregate_metrics.get("reasoning_depth", 0)
    total_changes = aggregate_metrics.get("total_changes", 0)
    
    # Positive observations (neutral descriptions)
    if approach_pattern in ["Deliberative", "Balanced"]:
        insights.append({
            "type": "positive",
            "label": "Took time to consider options",
            "icon": "check"
        })
    
    if reasoning_depth >= 30:
        insights.append({
            "type": "positive",
            "label": "Provided detailed reasoning text",
            "icon": "check"
        })
    
    if total_changes <= 2:
        insights.append({
            "type": "positive",
            "label": "Maintained initial selections",  # renamed from "Confident Decision Maker"
            "icon": "check"
        })
    
    # Neutral observations (informational, not warnings)
    if total_changes > 4:
        insights.append({
            "type": "neutral",  # changed from warning to neutral
            "label": "Revised selections multiple times",  # neutral description
            "icon": "info"
        })
    
    if reasoning_depth < 15:
        insights.append({
            "type": "neutral",  # changed from warning to neutral
            "label": "Explanations were concise",  # neutral phrasing
            "icon": "info"
        })
    
    if approach_pattern == "Iterative":
        insights.append({
            "type": "neutral",
            "label": "Explored multiple options before finalizing",
            "icon": "info"
        })
    
    # Ensure at least 3 insights
    if len(insights) < 3:
        insights.append({
            "type": "positive",
            "label": "Completed tasks in allocated time",
            "icon": "check"
        })
    
    return insights[:5]  # Max 5 insights


# ============================================================================
# DECISION PATH ANALYSIS
# ============================================================================
def _compute_decision_path(events: List[Dict]) -> List[Dict]:
    """
    Compute decision path timeline from events.
    Shows stages: Evaluate Options -> Revised Choice -> Final Decision
    """
    if not events:
        return [
            {"stage": "evaluate_options", "label": "Evaluate Options", "status": "pending", "timestamp": None},
            {"stage": "revised_choice", "label": "Revised Choice", "status": "pending", "timestamp": None},
            {"stage": "final_decision", "label": "Final Decision", "status": "pending", "timestamp": None},
        ]
    
    # Track decision stages
    has_viewed_options = False
    has_selected = False
    has_changed = False
    has_completed = False
    
    first_selection_time = None
    last_change_time = None
    completion_time = None
    
    for event in events:
        event_type = event["event_type"]
        
        if event_type == EventType.OPTION_SELECTED.value:
            has_selected = True
            if first_selection_time is None:
                first_selection_time = event["timestamp"]
        elif event_type == EventType.OPTION_CHANGED.value:
            has_changed = True
            last_change_time = event["timestamp"]
        elif event_type == EventType.TASK_COMPLETED.value:
            has_completed = True
            completion_time = event["timestamp"]
    
    has_viewed_options = has_selected  # If selected, must have viewed
    
    path = [
        {
            "stage": "evaluate_options",
            "label": "Evaluate Options",
            "status": "completed" if has_viewed_options else "in_progress",
            "timestamp": first_selection_time.isoformat() if first_selection_time else None,
        },
        {
            "stage": "revised_choice",
            "label": "Revised Choice",
            "status": "completed" if has_changed else ("skipped" if has_completed else "pending"),
            "timestamp": last_change_time.isoformat() if last_change_time else None,
        },
        {
            "stage": "final_decision",
            "label": "Final Decision",
            "status": "completed" if has_completed else "pending",
            "timestamp": completion_time.isoformat() if completion_time else None,
        },
    ]
    
    return path


# ============================================================================
# ACTIVE & COMPLETED ASSESSMENTS
# ============================================================================
async def get_active_assessments(recruiter_id: Optional[str] = None) -> List[Dict]:
    """Get all currently active (in-progress) assessments with basic info."""
    attempts = get_attempts_collection()
    
    query = {"status": {"$in": [AttemptStatus.IN_PROGRESS.value, AttemptStatus.PENDING.value]}}
    if recruiter_id:
        query["created_by"] = recruiter_id
        
    cursor = attempts.find(query).sort("started_at", 1)  # Oldest first (upload order)
    
    result = []
    async for attempt in cursor:
        attempt_id = str(attempt["_id"])
        started_at = attempt.get("started_at")
        now = datetime.utcnow()
        
        if started_at:
            time_elapsed = (now - started_at).total_seconds()
        else:
            time_elapsed = 0
            
        # For active assessments, we compute a fresh score for the list view
        # This ensures the "points" aren't 0 while the candidate is working.
        try:
            metrics = await compute_live_metrics(attempt_id)
            overall_fit = metrics.get("overall_fit", {})
        except Exception as e:
            print(f"[WARNING] Failed to compute live metrics for active list: {e}")
            overall_fit = {}
        
        result.append({
            "id": attempt_id,
            "candidate": {
                "name": attempt["candidate_info"]["name"],
                "email": attempt["candidate_info"]["email"],
                "position": attempt["candidate_info"]["position"],
                "avatar": _get_initials(attempt["candidate_info"]["name"]),
            },
            "status": attempt["status"],
            "progress": {
                "current": attempt["current_task_index"] + 1,
                "total": len(attempt["task_ids"]),
            },
            "time_elapsed": _format_time(int(time_elapsed)),
            "started_at": started_at.isoformat() if started_at else None,
            "overall_fit": overall_fit,
        })
    
    return result


async def get_completed_assessments(limit: int = 10, recruiter_id: Optional[str] = None) -> List[Dict]:
    """Get recently completed assessments."""
    attempts = get_attempts_collection()
    
    query = {
        "status": {"$in": [AttemptStatus.COMPLETED.value, AttemptStatus.LOCKED.value]}
    }
    if recruiter_id:
        query["created_by"] = recruiter_id
    
    cursor = attempts.find(query).sort("completed_at", -1).limit(limit)
    
    result = []
    async for attempt in cursor:
        attempt_id = str(attempt["_id"])
        completed_at = attempt.get("completed_at")
        started_at = attempt.get("started_at")
        
        if completed_at and started_at:
            total_time = (completed_at - started_at).total_seconds()
        else:
            total_time = 0
            
        # Use cached metrics for list view (Performance fix)
        overall_fit = attempt.get("cached_overall_fit", {})
        
        result.append({
            "id": attempt_id,
            "candidate": {
                "name": attempt["candidate_info"]["name"],
                "email": attempt["candidate_info"]["email"],
                "position": attempt["candidate_info"]["position"],
                "avatar": _get_initials(attempt["candidate_info"]["name"]),
            },
            "status": attempt["status"],
            "total_tasks": len(attempt["task_ids"]),
            "time_completed": _format_time(int(total_time)),
            "completed_at": completed_at.isoformat() if completed_at else None,
            "overall_fit": overall_fit,
        })
    
    return result


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def _get_initials(name: str) -> str:
    """Get initials from a name."""
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    return "??"


def _format_time(seconds: int) -> str:
    """Format seconds as MM:SS."""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

