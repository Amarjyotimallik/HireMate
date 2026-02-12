"""
Population Statistics Service

Tracks aggregate metrics across all candidates to provide:
- Population baselines and percentiles
- Confidence intervals based on sample size
- Authenticity/gaming detection
- Comparative context for all metrics

This addresses the black-box audit issue of "metrics without baselines".
"""

import math
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database


# ============================================================================
# CONSTANTS
# ============================================================================

# Minimum samples before percentiles are meaningful
MIN_POPULATION_SIZE = 10

# Percentile breakpoints to store
PERCENTILE_KEYS = [10, 25, 50, 75, 90]

# Metrics to track population stats for
TRACKED_METRICS = [
    "selection_speed",          # Time to first selection
    "avg_response_time",        # Average response time per question
    "decision_changes",         # Number of selection changes
    "explanation_length",       # Word count in explanations
    "idle_time",                # Pause time before action
    "task_completion_rate",     # Completion percentage
    "session_continuity",       # Consistency across session
]


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

async def _get_stats_collection() -> AsyncIOMotorDatabase:
    """Get the population_stats collection."""
    db = get_database()
    return db["population_stats"]


async def _get_outcomes_collection() -> AsyncIOMotorDatabase:
    """Get the hiring_outcomes collection."""
    db = get_database()
    return db["hiring_outcomes"]


# ============================================================================
# POPULATION STATISTICS UPDATES
# ============================================================================

async def update_population_stats(metrics: dict, recruiter_id: str = None) -> None:
    """
    Update population statistics with a new candidate's metrics.
    Uses online algorithm for running mean and variance (Welford's method).
    
    Called after each assessment completion.
    """
    collection = await _get_stats_collection()
    
    for metric_name in TRACKED_METRICS:
        value = _extract_metric_value(metrics, metric_name)
        if value is None:
            continue
            
        # Get existing stats or create new
        existing = await collection.find_one({
            "metric_name": metric_name,
            "recruiter_id": recruiter_id  # Per-recruiter stats for privacy
        })
        
        if existing:
            # Welford's online algorithm for running mean and variance
            n = existing["count"] + 1
            old_mean = existing["mean"]
            old_m2 = existing.get("m2", 0)  # Sum of squared differences
            
            delta = value - old_mean
            new_mean = old_mean + delta / n
            delta2 = value - new_mean
            new_m2 = old_m2 + delta * delta2
            
            # Update percentile samples (keep last 1000 for accuracy)
            samples = existing.get("samples", [])
            samples.append(value)
            if len(samples) > 1000:
                samples = samples[-1000:]
            
            await collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "count": n,
                    "mean": new_mean,
                    "m2": new_m2,
                    "std_dev": math.sqrt(new_m2 / n) if n > 1 else 0,
                    "min": min(existing.get("min", value), value),
                    "max": max(existing.get("max", value), value),
                    "samples": samples,
                    "percentiles": _calculate_percentiles(samples),
                    "updated_at": datetime.utcnow()
                }}
            )
        else:
            # Create new stat entry
            await collection.insert_one({
                "metric_name": metric_name,
                "recruiter_id": recruiter_id,
                "count": 1,
                "mean": value,
                "m2": 0,
                "std_dev": 0,
                "min": value,
                "max": value,
                "samples": [value],
                "percentiles": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })


def _extract_metric_value(metrics: dict, metric_name: str) -> Optional[float]:
    """Extract a specific metric value from the metrics dict."""
    # Handle nested structures
    mappings = {
        "selection_speed": lambda m: m.get("metrics", {}).get("avg_response_time"),
        "avg_response_time": lambda m: m.get("metrics", {}).get("avg_response_time"),
        "decision_changes": lambda m: m.get("aggregate_metrics", {}).get("total_changes"),
        "explanation_length": lambda m: m.get("aggregate_metrics", {}).get("total_explanation_words"),
        "idle_time": lambda m: m.get("metrics", {}).get("idle_time"),
        "task_completion_rate": lambda m: m.get("skill_profile", {}).get("task_completion"),
        "session_continuity": lambda m: m.get("metrics", {}).get("session_continuity"),
    }
    
    extractor = mappings.get(metric_name)
    if extractor:
        value = extractor(metrics)
        if value is not None and isinstance(value, (int, float)):
            return float(value)
    return None


def _calculate_percentiles(samples: list) -> dict:
    """Calculate percentile values from samples."""
    if len(samples) < MIN_POPULATION_SIZE:
        return {}
    
    sorted_samples = sorted(samples)
    n = len(sorted_samples)
    
    percentiles = {}
    for p in PERCENTILE_KEYS:
        idx = int((p / 100) * (n - 1))
        percentiles[f"p{p}"] = sorted_samples[idx]
    
    return percentiles


# ============================================================================
# PERCENTILE CALCULATION
# ============================================================================

async def get_percentile(
    metric_name: str, 
    value: float, 
    recruiter_id: str = None
) -> Optional[int]:
    """
    Get the percentile rank for a given metric value.
    Returns 0-100 indicating what percentage of population this value exceeds.
    
    Example: percentile=78 means "better than 78% of candidates"
    """
    collection = await _get_stats_collection()
    
    stats = await collection.find_one({
        "metric_name": metric_name,
        "recruiter_id": recruiter_id
    })
    
    if not stats or stats["count"] < MIN_POPULATION_SIZE:
        return None  # Not enough data for meaningful percentile
    
    samples = stats.get("samples", [])
    if not samples:
        return None
    
    # Count how many samples this value exceeds
    count_below = sum(1 for s in samples if s < value)
    percentile = int((count_below / len(samples)) * 100)
    
    return percentile


async def get_all_percentiles(
    metrics: dict, 
    recruiter_id: str = None
) -> dict:
    """
    Get percentile ranks for all tracked metrics.
    Returns dict like: {"selection_speed": 78, "explanation_length": 45, ...}
    """
    percentiles = {}
    
    for metric_name in TRACKED_METRICS:
        value = _extract_metric_value(metrics, metric_name)
        if value is not None:
            pct = await get_percentile(metric_name, value, recruiter_id)
            if pct is not None:
                percentiles[metric_name] = pct
    
    return percentiles


# ============================================================================
# CONFIDENCE INTERVALS
# ============================================================================

def calculate_confidence_interval(
    value: float,
    sample_size: int,
    population_std: float = None
) -> tuple:
    """
    Calculate 95% confidence interval for a metric.
    
    Returns (lower_bound, upper_bound).
    Wider interval = more uncertainty.
    """
    if sample_size < 2:
        # With 1 sample, uncertainty is maximum
        return (value * 0.5, value * 1.5)
    
    # Use default std if not provided
    if population_std is None:
        population_std = value * 0.3  # Assume 30% coefficient of variation
    
    # Standard error
    se = population_std / math.sqrt(sample_size)
    
    # 95% confidence interval (z = 1.96)
    margin = 1.96 * se
    
    return (max(0, value - margin), value + margin)


async def get_confidence_intervals(
    metrics: dict,
    tasks_completed: int,
    recruiter_id: str = None
) -> dict:
    """
    Get confidence intervals for all metrics based on sample size.
    """
    collection = await _get_stats_collection()
    intervals = {}
    
    for metric_name in TRACKED_METRICS:
        value = _extract_metric_value(metrics, metric_name)
        if value is None:
            continue
        
        # Get population std dev
        stats = await collection.find_one({
            "metric_name": metric_name,
            "recruiter_id": recruiter_id
        })
        
        pop_std = stats.get("std_dev") if stats else None
        
        lower, upper = calculate_confidence_interval(value, tasks_completed, pop_std)
        
        intervals[metric_name] = {
            "value": round(value, 2),
            "lower": round(lower, 2),
            "upper": round(upper, 2),
            "uncertainty": round((upper - lower) / max(value, 1) * 100, 1)  # % uncertainty
        }
    
    return intervals


# ============================================================================
# BEHAVIORAL CONSISTENCY ANALYSIS (Renamed from "Anti-Cheat" / "Gaming Detection")
# ============================================================================

def compute_behavioral_consistency(per_task_metrics: list, anti_cheat_metrics: dict = None) -> dict:
    """
    Analyze behavioral consistency patterns to identify anomalies.
    
    This is NOT a "cheating detector" — it flags behavioral patterns that deviate
    from typical independent problem-solving. These patterns may have innocent
    explanations (e.g., using notes, taking breaks) or may indicate external assistance.
    
    Returns score 0-100 where:
    - 100 = Natural, varied behavior consistent with independent work
    - 0 = Highly anomalous patterns requiring review
    
    Also returns flags explaining any observations with DETAILED explanations
    and MULTIPLE possible interpretations (not accusations).
    
    Args:
        per_task_metrics: List of per-task behavioral metrics
        anti_cheat_metrics: Dict with keys: focus_loss_count, paste_count, copy_count, long_idle_count
    """
    if not per_task_metrics or len(per_task_metrics) < 2:
        return {
            "score": 100,
            "flags": [],
            "status": "insufficient_data",
            "confidence_explanation": {
                "level": "low",
                "reason": f"Only {len(per_task_metrics) if per_task_metrics else 0} questions analyzed. Need at least 3 for reliable pattern detection.",
                "data_points": len(per_task_metrics) if per_task_metrics else 0
            }
        }
    
    flags = []
    deductions = 0
    total_data_points = len(per_task_metrics)
    anti_cheat = anti_cheat_metrics or {}
    
    # ===== BEHAVIORAL CONSISTENCY CHECKS (Multiple Interpretations) =====
    # Check A: Paste Detection (rapid text entry)
    paste_count = anti_cheat.get("paste_count", 0)
    if paste_count > 0:
        severity = "medium" if paste_count >= 2 else "low"
        deduction_amount = min(15, paste_count * 5)  # Reduced from 25 max to 15 max
        flags.append({
            "flag": "rapid_text_entry",
            "title": "Rapid Text Entry Detected",
            "description": f"Text appeared rapidly {paste_count} time(s) during the assessment.",
            "severity": severity,
            "deduction": deduction_amount,
            "evidence": {
                "what_we_found": f"{paste_count} paste event(s) detected in reasoning fields",
                "possible_explanations": [
                    "Candidate pasted from personal notes they prepared",
                    "Candidate used auto-fill or text expansion tool",
                    "Candidate copied from an external source"
                ],
                "what_is_normal": "Most candidates type reasoning directly, but pasting prepared notes is not uncommon.",
                "recommendation": "Review explanation quality. Well-reasoned pasted content may indicate preparation; generic content may indicate external assistance."
            }
        })
        deductions += deduction_amount
    
    # Check B: Focus Changes (Window/Tab Navigation)
    focus_loss_count = anti_cheat.get("focus_loss_count", 0)
    if focus_loss_count > 3:
        severity = "medium" if focus_loss_count >= 6 else "low"
        deduction_amount = min(10, (focus_loss_count - 3) * 2)  # Reduced: -2 per switch after first 3, max -10
        flags.append({
            "flag": "window_navigation",
            "title": "Multiple Window/Tab Switches",
            "description": f"Candidate navigated away from assessment window {focus_loss_count} times.",
            "severity": severity,
            "deduction": deduction_amount,
            "evidence": {
                "what_we_found": f"{focus_loss_count} focus loss events (tab switches or window changes)",
                "possible_explanations": [
                    "Candidate checked email, calendar, or messaging app",
                    "Candidate looked up information on company or role",
                    "Candidate used external resources for answers"
                ],
                "what_is_normal": "1-3 brief switches (checking time, notifications) are common. Extended absences are more notable than frequency.",
                "recommendation": "Consider total time away, not just count. Brief switches (<5s) are typically benign."
            }
        })
        deductions += deduction_amount
    
    # Check C: Content Copying
    copy_count = anti_cheat.get("copy_count", 0)
    if copy_count > 0:
        severity = "low"  # Reduced severity
        deduction_amount = min(8, copy_count * 4)  # Reduced: -4 per copy, max -8
        flags.append({
            "flag": "content_copied",
            "title": "Assessment Content Copied",
            "description": f"Candidate copied assessment content {copy_count} time(s).",
            "severity": severity,
            "deduction": deduction_amount,
            "evidence": {
                "what_we_found": f"{copy_count} copy event(s) detected on question content",
                "possible_explanations": [
                    "Candidate copied question to reference while writing notes",
                    "Candidate saved question for personal records",
                    "Candidate copied to feed to an external tool"
                ],
                "what_is_normal": "Copying is uncommon but not inherently suspicious. Context matters more than count.",
                "recommendation": "Consider if candidate also showed paste events (suggesting external tool use) or if copying was followed by extended pauses."
            }
        })
        deductions += deduction_amount

    # --- Check 1: Response Time Variation ---
    times = [m.get("time_spent_seconds", 0) for m in per_task_metrics if m.get("time_spent_seconds")]
    timing_analysis = None
    if len(times) >= 3:
        mean_time = sum(times) / len(times)
        if mean_time > 0:
            variance = sum((t - mean_time) ** 2 for t in times) / len(times)
            std_dev = math.sqrt(variance)
            cv = std_dev / mean_time  # Coefficient of variation
            
            timing_analysis = {
                "mean_seconds": round(mean_time, 1),
                "std_deviation": round(std_dev, 1),
                "coefficient_of_variation": round(cv * 100, 1),
                "range": f"{round(min(times), 1)}s - {round(max(times), 1)}s"
            }
            
            if cv < 0.1:  # Less than 10% variation is unusual
                flags.append({
                    "flag": "low_timing_variation",
                    "title": "Low Variation in Response Times",
                    "description": "Response times show less variation than typically observed.",
                    "severity": "low",
                    "deduction": 8,  # Reduced from 15
                    "evidence": {
                        "what_we_found": f"All {len(times)} responses took between {round(min(times), 1)}s and {round(max(times), 1)}s",
                        "average_time": f"{round(mean_time, 1)} seconds",
                        "variation": f"Only {round(cv * 100, 1)}% variation (typical range: 15-60%)",
                        "standard_deviation": f"±{round(std_dev, 1)} seconds",
                        "possible_explanations": [
                            "Candidate is very practiced with this question type",
                            "Questions were similar in difficulty and format",
                            "Candidate used a consistent timing strategy",
                            "Responses may have been rehearsed or scripted"
                        ],
                        "what_is_normal": "Most candidates vary by 10-30 seconds between questions due to varying complexity."
                    }
                })
                deductions += 8
    
    # --- Check 2: Rapid Decisions Without Revision ---
    changes = [m.get("decision_changes", 0) for m in per_task_metrics]
    first_decisions = [m.get("first_decision_speed_seconds", 0) for m in per_task_metrics]
    
    avg_first_decision = sum(first_decisions) / len(first_decisions) if first_decisions else 0
    total_changes = sum(changes)
    
    if all(c == 0 for c in changes) and all(f < 5 for f in first_decisions if f):
        flags.append({
            "flag": "rapid_commitment_pattern",
            "title": "Rapid Commitment Pattern",
            "description": "Candidate made quick initial decisions without revising any answers.",
            "severity": "low",  # Reduced from high
            "deduction": 10,  # Reduced from 25
            "evidence": {
                "what_we_found": f"Zero answer changes across {len(changes)} questions with avg first decision in {round(avg_first_decision, 1)}s",
                "decision_changes": f"{total_changes} total revisions (0 per question)",
                "first_decision_speed": f"Average {round(avg_first_decision, 1)}s (all under 5s)",
                "possible_explanations": [
                    "Candidate has strong domain expertise and high confidence",
                    "Candidate is familiar with this question format",
                    "Candidate made snap judgments without full consideration",
                    "Responses may have been prepared in advance"
                ],
                "what_is_normal": "Most candidates change 1-2 answers and take 5-15s for initial selections, but expertise can explain faster commitment."
            }
        })
        deductions += 10
    
    # --- Check 3: Explanation Length Uniformity ---
    word_counts = [m.get("word_count", 0) for m in per_task_metrics if m.get("word_count")]
    if len(word_counts) >= 3:
        unique_counts = len(set(word_counts))
        avg_words = sum(word_counts) / len(word_counts)
        if unique_counts == 1:
            flags.append({
                "flag": "uniform_explanation_length",
                "title": "Uniform Explanation Lengths",
                "description": "All explanations have identical word counts.",
                "severity": "low",  # Reduced from medium
                "deduction": 5,  # Reduced from 15
                "evidence": {
                    "what_we_found": f"All {len(word_counts)} explanations contain exactly {word_counts[0]} words",
                    "word_counts": f"[{', '.join(str(w) for w in word_counts[:5])}]",
                    "variation": "0% variation in length",
                    "possible_explanations": [
                        "Candidate used a template or structured format for responses",
                        "Questions were similar in scope requiring similar explanation lengths",
                        "Candidate has a consistent communication style",
                        "Responses may have been pre-written to a specific length"
                    ],
                    "what_is_normal": "Typical responses show 30-50% variation in length based on question complexity."
                }
            })
            deductions += 5
    
    # --- Check 4: Pause Pattern Analysis ---
    idle_times = [m.get("idle_time_seconds", 0) for m in per_task_metrics if m.get("idle_time_seconds")]
    if len(idle_times) >= 3:
        for base in [5, 10, 15]:
            aligned_count = sum(1 for t in idle_times if t > base and abs(t % base) < 0.5)
            if aligned_count >= len(idle_times) * 0.7:
                flags.append({
                    "flag": "patterned_pauses",
                    "title": f"Aligned Pause Intervals ({base}s)",
                    "description": f"Multiple pause times align to {base}-second intervals.",
                    "severity": "low",
                    "deduction": 5,  # Reduced from 10
                    "evidence": {
                        "what_we_found": f"{aligned_count} of {len(idle_times)} pauses align to {base}s intervals",
                        "idle_times": f"[{', '.join(str(round(t, 1)) for t in idle_times[:5])}]s",
                        "pattern_strength": f"{round(aligned_count / len(idle_times) * 100)}% alignment",
                        "possible_explanations": [
                            "Candidate used a timing strategy (e.g., 'think for 10 seconds')",
                            "Candidate was taking breaks at regular intervals",
                            "Questions had similar complexity requiring similar thinking time",
                            "Pauses may have been coached or scripted"
                        ],
                        "what_is_normal": "Natural thinking pauses are typically irregular, varying with question complexity."
                    }
                })
                deductions += 5
                break
    
    # --- Check 5: Approach Pattern Variation ---
    patterns = [m.get("observed_pattern", "") for m in per_task_metrics]
    patterns_filtered = [p for p in patterns if p]
    if len(patterns_filtered) >= 4 and len(set(patterns_filtered)) == 1:
        flags.append({
            "flag": "single_approach_pattern",
            "title": "Consistent Approach Pattern",
            "description": "Candidate used the same behavioral approach on all questions.",
            "severity": "low",
            "deduction": 3,  # Reduced from 10
            "evidence": {
                "what_we_found": f"Pattern '{patterns_filtered[0]}' on all {len(patterns_filtered)} questions",
                "unique_patterns": f"1 (typical range: 2-4)",
                "possible_explanations": [
                    "Candidate has a well-established problem-solving methodology",
                    "Questions were similar in type, warranting consistent approach",
                    "Candidate was following a specific strategy or framework",
                    "Approach may have been coached or rehearsed"
                ],
                "what_is_normal": "Most candidates adapt their approach slightly based on question type, but consistency can indicate expertise."
            }
        })
        deductions += 3
    
    score = max(0, 100 - deductions)
    
    # Build confidence explanation with safer terminology
    if score >= 85:
        status = "consistent_with_independent_work"
        conf_level, conf_reason = "high", f"Analyzed {total_data_points} responses with natural variation typical of independent problem-solving."
    elif score >= 60:
        status = "some_observations_noted"
        conf_level, conf_reason = "moderate", f"Some patterns in {total_data_points} responses. {len(flags)} observations noted for review."
    else:
        status = "review_recommended"
        conf_level, conf_reason = "lower_confidence", f"Multiple patterns in {total_data_points} responses. {len(flags)} observations warrant additional review."
    
    return {
        "score": score,
        "flags": flags,
        "status": status,
        "assessment": "Behavioral Consistency Analysis",  # Renamed from "Authenticity Score"
        "confidence_explanation": {
            "level": conf_level,
            "reason": conf_reason,
            "data_points": total_data_points,
            "observations": len(flags),
            "total_adjustments": deductions,
            "factors_analyzed": [
                {"name": "Response Time Variation", "analyzed": len(times) >= 3, "data": timing_analysis},
                {"name": "Decision Revision Pattern", "analyzed": True, "avg_changes": round(sum(changes) / len(changes), 1) if changes else 0},
                {"name": "Explanation Length Variety", "analyzed": len(word_counts) >= 3, "unique_lengths": len(set(word_counts)) if word_counts else 0},
                {"name": "Pause Pattern Analysis", "analyzed": len(idle_times) >= 3, "samples": len(idle_times)},
                {"name": "Approach Variation", "analyzed": len(patterns_filtered) >= 4, "unique_patterns": len(set(patterns_filtered)) if patterns_filtered else 0}
            ],
            "interpretation": _get_score_interpretation(score, flags)
        }
    }


def _get_score_interpretation(score: int, flags: list) -> str:
    """Generate human-readable interpretation of the behavioral consistency score."""
    high_count = sum(1 for f in flags if f.get("severity") == "high")
    medium_count = sum(1 for f in flags if f.get("severity") == "medium")
    
    if score >= 90:
        return "Behavioral patterns are consistent with independent problem-solving. No significant observations."
    elif score >= 75:
        return "Behavioral patterns show minor variations within normal range. Some unique responding styles observed."
    elif score >= 60:
        if high_count > 0:
            return f"Some notable patterns detected ({high_count} higher-observation). Review recommended to understand context."
        return "Some patterns observed that differ from typical independent work. May reflect unique style or external factors."
    else:
        return "Multiple behavioral patterns noted that differ from typical independent problem-solving. Additional review suggested to understand context (e.g., using notes, external resources, or unique approach)."


# ============================================================================
# POPULATION CONTEXT (Human-readable summaries)
# ============================================================================

async def get_population_context(
    percentiles: dict,
    recruiter_id: str = None
) -> dict:
    """
    Generate human-readable context for percentile data.
    
    Example output:
    {
        "selection_speed": "Faster than 78% of candidates",
        "explanation_length": "More detailed than 65% of candidates"
    }
    """
    context = {}
    
    templates = {
        "selection_speed": {
            "high": "Faster than {pct}% of candidates",
            "low": "Takes more time than {pct}% of candidates"
        },
        "avg_response_time": {
            "high": "Quicker responses than {pct}% of candidates",
            "low": "More deliberate than {pct}% of candidates"
        },
        "explanation_length": {
            "high": "More detailed explanations than {pct}% of candidates",
            "low": "More concise than {pct}% of candidates"
        },
        "decision_changes": {
            "high": "More exploratory than {pct}% of candidates",
            "low": "More decisive than {pct}% of candidates"
        },
        "session_continuity": {
            "high": "More consistent than {pct}% of candidates",
            "low": "More variable than {pct}% of candidates"
        }
    }
    
    for metric, pct in percentiles.items():
        if metric in templates:
            # Determine direction (some metrics high=good, some low=good)
            direction = "high" if pct >= 50 else "low"
            display_pct = pct if pct >= 50 else (100 - pct)
            
            template = templates[metric][direction]
            context[metric] = template.format(pct=display_pct)
    
    return context


# ============================================================================
# OUTCOME TRACKING (For future calibration)
# ============================================================================

async def log_hiring_decision(
    attempt_id: str,
    decision: str,  # "hire", "no_hire", "pending"
    recruiter_id: str,
    metrics_snapshot: dict = None,
    notes: str = None
) -> dict:
    """
    Log a hiring decision for future calibration studies.
    
    This allows correlation between HireMate predictions and actual outcomes.
    """
    collection = await _get_outcomes_collection()
    
    outcome = {
        "attempt_id": attempt_id,
        "decision": decision,
        "recruiter_id": recruiter_id,
        "metrics_snapshot": metrics_snapshot or {},
        "notes": notes,
        "decision_date": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }
    
    # Upsert to allow decision updates
    result = await collection.update_one(
        {"attempt_id": attempt_id},
        {"$set": outcome},
        upsert=True
    )
    
    return {"status": "logged", "attempt_id": attempt_id}


async def get_calibration_stats(recruiter_id: str = None) -> dict:
    """
    Get calibration statistics for a recruiter's decisions.
    
    Shows how predictions correlate with actual hiring decisions.
    (Note: Meaningful only after significant outcome data is collected)
    """
    collection = await _get_outcomes_collection()
    
    query = {}
    if recruiter_id:
        query["recruiter_id"] = recruiter_id
    
    total = await collection.count_documents(query)
    hired = await collection.count_documents({**query, "decision": "hire"})
    rejected = await collection.count_documents({**query, "decision": "no_hire"})
    pending = await collection.count_documents({**query, "decision": "pending"})
    
    return {
        "total_decisions": total,
        "hired": hired,
        "rejected": rejected,
        "pending": pending,
        "calibration_ready": total >= 50,  # Need 50+ decisions for meaningful calibration
        "message": "Collect more outcomes to enable calibration analysis" if total < 50 else "Ready for calibration analysis"
    }
