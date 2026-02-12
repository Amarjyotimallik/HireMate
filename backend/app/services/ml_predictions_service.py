"""
ML Predictions orchestrator: interview success, job-fit, behavioral traits.
Fetches attempt metrics (and optional resume), calls prediction models.
"""

from typing import Dict, Any, Optional

from app.services.metrics_service import get_metrics
from app.services.attempt_service import get_attempt_by_id
from app.services.ats_score_service import calculate_ats_score
from app.services.interview_success_model import predict as predict_interview_success
from app.services.behavioral_pattern_model import predict_traits as predict_behavioral_traits


async def get_interview_success_prediction(
    attempt_id: str,
    include_resume: bool = True,
) -> Dict[str, Any]:
    """
    Get interview success probability for an attempt.
    Uses computed metrics; if include_resume and attempt has resume_text, blends in ATS-style score.
    """
    metrics = await get_metrics(attempt_id)
    if not metrics:
        return {
            "probability": 0.0,
            "confidence": "low",
            "factors": [],
            "message": "No computed metrics for this attempt. Complete the assessment and compute metrics first.",
        }

    # Build features from ComputedMetricsResponse
    global_m = metrics.global_metrics
    agg = metrics.aggregated_patterns
    per_task = metrics.per_task_metrics

    total_tasks = global_m.total_tasks or 1
    tasks_completed = global_m.tasks_completed
    completion_rate = tasks_completed / total_tasks if total_tasks else 0

    # Decision firmness: fewer option changes = higher
    if per_task:
        avg_changes = sum(m.decision_change_count for m in per_task) / len(per_task)
        decision_firmness = max(0, 100 - min(100, avg_changes * 25))
    else:
        decision_firmness = 50

    reasoning_depth = (agg.reasoning_engagement * 100) if agg else 50

    features = {
        "decision_firmness": decision_firmness,
        "reasoning_depth": reasoning_depth,
        "completion_rate": completion_rate,
        "attention_stability": agg.attention_stability if agg else 0.5,
        "decision_consistency": agg.decision_consistency if agg else 0.5,
        "total_tasks": total_tasks,
        "tasks_completed": tasks_completed,
    }

    ats_score = None
    if include_resume:
        attempt = await get_attempt_by_id(attempt_id)
        if attempt and attempt.candidate_info and getattr(attempt.candidate_info, "resume_text", None) and (attempt.candidate_info.resume_text or "").strip():
            # Use ATS score vs empty JD (formatting + resume quality proxy) or we could skip JD
            ats_result = calculate_ats_score(attempt.candidate_info.resume_text, "")
            ats_score = ats_result.get("ats_score", 0)
            features["ats_score"] = ats_score

    result = predict_interview_success(features)
    return result


async def get_behavioral_prediction(attempt_id: str) -> Dict[str, Any]:
    """Get predicted behavioral traits for an attempt from its computed metrics."""
    metrics = await get_metrics(attempt_id)
    if not metrics:
        return {
            "predicted_traits": [],
            "confidence": "low",
            "message": "No computed metrics for this attempt.",
        }

    metrics_data = {
        "aggregated_patterns": metrics.aggregated_patterns.model_dump() if metrics.aggregated_patterns else {},
        "global_metrics": metrics.global_metrics.model_dump() if metrics.global_metrics else {},
        "per_task_metrics": [m.model_dump() for m in metrics.per_task_metrics],
    }
    return predict_behavioral_traits(metrics_data)


async def get_job_fit_prediction(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Job fit score (resume vs JD). Delegates to ATS score + breakdown."""
    result = calculate_ats_score(resume_text, job_description)
    return {
        "fit_score": result["ats_score"],
        "breakdown": result["breakdown"],
        "suggestions": [f.get("fix", "") for f in result.get("formatting_issues", [])[:5]],
    }
