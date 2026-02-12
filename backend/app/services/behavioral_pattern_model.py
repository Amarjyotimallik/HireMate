"""
Behavioral pattern predictor: map metrics to predicted traits (e.g. "Decisive under pressure").
Rule-based from aggregated_patterns and per_task metrics; no training data required.
"""

from typing import Dict, Any, List


def predict_traits(metrics_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive predicted behavioral traits from computed metrics.
    metrics_data: dict with aggregated_patterns, global_metrics, per_task_metrics (or equivalent).
    Returns predicted_traits (list of strings), confidence (high/medium/low).
    """
    traits: List[str] = []
    agg = metrics_data.get("aggregated_patterns") or {}
    global_m = metrics_data.get("global_metrics") or {}
    per_task = metrics_data.get("per_task_metrics") or []

    decision_consistency = agg.get("decision_consistency", 0.5)
    reasoning_engagement = agg.get("reasoning_engagement", 0)
    attention_stability = agg.get("attention_stability", 0.5)
    risk_pref = agg.get("risk_preference") or {}
    dominant_risk = (risk_pref.get("dominant") or "balanced").lower()

    total_tasks = global_m.get("total_tasks", 0) or 1
    tasks_completed = global_m.get("tasks_completed", 0)
    completion_rate = tasks_completed / total_tasks if total_tasks else 0

    # Decision firmness from average option changes per task
    if per_task:
        avg_changes = sum(m.get("decision_change_count", 0) for m in per_task) / len(per_task)
        decision_firmness = max(0, 100 - min(100, avg_changes * 25))
    else:
        decision_firmness = 50
        avg_changes = 0

    # Trait rules
    if decision_firmness >= 75:
        traits.append("Likely decisive under pressure")
    elif decision_firmness >= 50:
        traits.append("Moderately decisive; may revisit choices")
    else:
        traits.append("Tends to revise decisions frequently")

    if reasoning_engagement >= 0.6:
        traits.append("Thoughtful reasoner; provides detailed explanations")
    elif reasoning_engagement >= 0.3:
        traits.append("Moderate reasoning depth")
    else:
        traits.append("Concise or minimal reasoning")

    if attention_stability >= 0.8:
        traits.append("High focus stability")
    elif attention_stability >= 0.5:
        traits.append("Generally focused")
    else:
        traits.append("May have attention shifts during assessment")

    if decision_consistency >= 0.7:
        traits.append("Consistent decision speed across questions")
    elif decision_consistency >= 0.4:
        traits.append("Variable pacing across tasks")

    if dominant_risk == "low":
        traits.append("Risk-averse preference in choices")
    elif dominant_risk == "high":
        traits.append("Risk-tolerant preference in choices")
    else:
        traits.append("Balanced risk preference")

    if completion_rate >= 0.9:
        traits.append("Strong task completion")
    elif completion_rate >= 0.5:
        traits.append("Partial completion")

    # Confidence
    if tasks_completed >= 3 and total_tasks >= 3:
        confidence = "high"
    elif tasks_completed >= 1:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "predicted_traits": traits,
        "confidence": confidence,
    }
