"""
Baseline Comparison Service

Implements candidate-level baseline comparison for authenticity analysis.
Instead of comparing to population averages (which risks bias), this service
compares a candidate's behavior to their OWN baseline from previous assessments.

Audit Requirement (Layer 4):
- "Does this behavior significantly deviate from the candidate's own baseline?"
- Baseline comparison = defensible
- Population comparison = risky (for primary authenticity judgment)

Key Principles:
1. First-time candidates get "no baseline available" not "suspicious"
2. Returning candidates are compared to their own history
3. Population data is used for CONTEXT only, not judgment
"""

from datetime import datetime
from typing import Dict, List, Optional
from statistics import mean, stdev

from app.db import get_database


async def _get_baselines_collection():
    """Get the candidate_baselines collection."""
    db = get_database()
    return db["candidate_baselines"]


async def get_candidate_baseline(candidate_email: str) -> Optional[Dict]:
    """
    Retrieve a candidate's behavioral baseline from previous assessments.
    
    Returns None if no previous assessments exist (first-time candidate).
    """
    collection = await _get_baselines_collection()
    baseline = await collection.find_one({"candidate_email": candidate_email})
    return baseline


async def update_candidate_baseline(
    candidate_email: str,
    per_task_metrics: List[Dict],
    aggregate_metrics: Dict
) -> Dict:
    """
    Update a candidate's behavioral baseline after assessment completion.
    
    Uses running averages so baseline evolves with each assessment.
    """
    collection = await _get_baselines_collection()
    
    existing = await collection.find_one({"candidate_email": candidate_email})
    
    # Extract key behavioral metrics
    times = [m.get("time_spent_seconds", 0) for m in per_task_metrics if m.get("time_spent_seconds")]
    changes = [m.get("decision_changes", 0) for m in per_task_metrics]
    explanations = [m.get("explanation_word_count", 0) for m in per_task_metrics]
    
    new_metrics = {
        "avg_response_time": mean(times) if times else 0,
        "avg_decision_changes": mean(changes) if changes else 0,
        "avg_explanation_length": mean(explanations) if explanations else 0,
        "timing_variance": stdev(times) if len(times) >= 2 else 0,
        "total_tasks_completed": len([m for m in per_task_metrics if m.get("is_completed")]),
    }
    
    if existing:
        # Update running averages (weighted toward recent)
        n = existing.get("assessment_count", 1)
        weight_new = 0.4  # Give 40% weight to new assessment
        weight_old = 0.6  # Give 60% weight to historical baseline
        
        updated_baseline = {}
        for key in new_metrics:
            old_val = existing.get("baseline_metrics", {}).get(key, new_metrics[key])
            updated_baseline[key] = (old_val * weight_old) + (new_metrics[key] * weight_new)
        
        await collection.update_one(
            {"candidate_email": candidate_email},
            {"$set": {
                "baseline_metrics": updated_baseline,
                "assessment_count": n + 1,
                "last_assessment_metrics": new_metrics,
                "last_updated": datetime.utcnow(),
            }}
        )
        
        return {
            "status": "updated",
            "assessment_count": n + 1,
            "baseline_metrics": updated_baseline,
        }
    else:
        # Create new baseline
        await collection.insert_one({
            "candidate_email": candidate_email,
            "baseline_metrics": new_metrics,
            "assessment_count": 1,
            "last_assessment_metrics": new_metrics,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
        })
        
        return {
            "status": "created",
            "assessment_count": 1,
            "baseline_metrics": new_metrics,
        }


async def compare_to_baseline(
    candidate_email: str,
    current_metrics: Dict,
    per_task_metrics: List[Dict]
) -> Dict:
    """
    Compare current assessment behavior to candidate's own baseline.
    
    Returns comparison results with context, NOT accusations.
    
    If no baseline exists (first assessment), returns "no_baseline" status
    with a recommendation for follow-up assessment.
    """
    baseline = await get_candidate_baseline(candidate_email)
    
    if not baseline:
        return {
            "status": "no_baseline",
            "message": (
                "This is the candidate's first assessment. No personal baseline available. "
                "Behavioral patterns will be compared to general population context only. "
                "Consider a follow-up assessment for more reliable comparison."
            ),
            "confidence": "low",
            "deviations": [],
            "recommendation": "First assessment - establish baseline for future comparison",
        }
    
    baseline_metrics = baseline.get("baseline_metrics", {})
    assessment_count = baseline.get("assessment_count", 1)
    
    # Compare current to baseline
    deviations = []
    
    # Extract current metrics
    times = [m.get("time_spent_seconds", 0) for m in per_task_metrics if m.get("time_spent_seconds")]
    current_avg_time = mean(times) if times else 0
    current_timing_variance = stdev(times) if len(times) >= 2 else 0
    
    changes = [m.get("decision_changes", 0) for m in per_task_metrics]
    current_avg_changes = mean(changes) if changes else 0
    
    explanations = [m.get("explanation_word_count", 0) for m in per_task_metrics]
    current_avg_explanation = mean(explanations) if explanations else 0
    
    # Check response time deviation
    baseline_time = baseline_metrics.get("avg_response_time", 0)
    if baseline_time > 0 and current_avg_time > 0:
        time_ratio = current_avg_time / baseline_time
        if time_ratio < 0.5 or time_ratio > 2.0:
            deviations.append({
                "metric": "response_time",
                "baseline_value": round(baseline_time, 1),
                "current_value": round(current_avg_time, 1),
                "deviation": f"{abs(1 - time_ratio) * 100:.0f}% {'faster' if time_ratio < 1 else 'slower'} than baseline",
                "possible_explanations": [
                    "Different question difficulty level",
                    "Candidate is more/less familiar with this topic",
                    "Different testing conditions (time of day, environment)",
                    "Candidate's approach has evolved",
                ],
                "severity": "notable" if 0.3 < time_ratio < 3.0 else "significant",
            })
    
    # Check decision change deviation
    baseline_changes = baseline_metrics.get("avg_decision_changes", 0)
    change_diff = abs(current_avg_changes - baseline_changes)
    if change_diff > 2:
        deviations.append({
            "metric": "decision_changes",
            "baseline_value": round(baseline_changes, 1),
            "current_value": round(current_avg_changes, 1),
            "deviation": f"{change_diff:.1f} more changes per task than baseline",
            "possible_explanations": [
                "Questions were more ambiguous or challenging",
                "Candidate was more exploratory this time",
                "Candidate was less certain about domain",
            ],
            "severity": "notable",
        })
    
    # Check explanation length deviation
    baseline_explanation = baseline_metrics.get("avg_explanation_length", 0)
    if baseline_explanation > 0 and current_avg_explanation > 0:
        explanation_ratio = current_avg_explanation / baseline_explanation
        if explanation_ratio < 0.4 or explanation_ratio > 2.5:
            deviations.append({
                "metric": "explanation_length",
                "baseline_value": round(baseline_explanation, 1),
                "current_value": round(current_avg_explanation, 1),
                "deviation": f"{abs(1 - explanation_ratio) * 100:.0f}% {'shorter' if explanation_ratio < 1 else 'longer'} than baseline",
                "possible_explanations": [
                    "Different question types requiring different explanation depth",
                    "Candidate was more/less engaged this session",
                    "Time pressure affected explanation detail",
                ],
                "severity": "notable",
            })
    
    # Check timing variance deviation
    baseline_variance = baseline_metrics.get("timing_variance", 0)
    if baseline_variance > 0 and current_timing_variance > 0:
        variance_ratio = current_timing_variance / baseline_variance
        if variance_ratio < 0.3:
            deviations.append({
                "metric": "timing_consistency",
                "baseline_value": round(baseline_variance, 1),
                "current_value": round(current_timing_variance, 1),
                "deviation": "Significantly more uniform timing than baseline",
                "possible_explanations": [
                    "Questions were similar in difficulty",
                    "Candidate developed a consistent strategy",
                    "Timing may have been externally regulated",
                ],
                "severity": "notable",
            })
    
    # Determine overall comparison
    significant_deviations = [d for d in deviations if d["severity"] == "significant"]
    notable_deviations = [d for d in deviations if d["severity"] == "notable"]
    
    if len(significant_deviations) >= 2:
        status = "significant_deviation"
        message = (
            f"Behavior differs significantly from this candidate's baseline across "
            f"{len(significant_deviations)} dimensions. This may warrant a conversation "
            f"with the candidate to understand context."
        )
        confidence = "moderate" if assessment_count >= 3 else "low"
    elif len(deviations) > 0:
        status = "some_deviation"
        message = (
            f"Some behavioral differences from baseline noted ({len(deviations)} dimensions). "
            f"These are within the range of normal variation between sessions."
        )
        confidence = "moderate"
    else:
        status = "consistent_with_baseline"
        message = "Behavior is consistent with this candidate's established baseline."
        confidence = "high" if assessment_count >= 3 else "moderate"
    
    return {
        "status": status,
        "message": message,
        "confidence": confidence,
        "assessment_count": assessment_count,
        "deviations": deviations,
        "baseline_summary": {
            "assessments_in_baseline": assessment_count,
            "avg_response_time": round(baseline_metrics.get("avg_response_time", 0), 1),
            "avg_decision_changes": round(baseline_metrics.get("avg_decision_changes", 0), 1),
            "avg_explanation_length": round(baseline_metrics.get("avg_explanation_length", 0), 1),
        },
        "recommendation": (
            "Consistent behavior observed" if status == "consistent_with_baseline"
            else "Review deviations in context of role and question difficulty"
        ),
    }
