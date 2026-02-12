"""
False Positive Protection Service

This service implements safeguards against incorrectly flagging legitimate candidates.
It provides confidence scoring, uncertainty quantification, and human override mechanisms.

Key Principles:
1. Humility - We acknowledge uncertainty in our analysis
2. Transparency - All confidence factors are exposed
3. Override - Recruiters can always override system recommendations
4. Context - Multiple explanations are provided, not accusations
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from statistics import stdev, mean
import math


class FalsePositiveProtection:
    """
    Built-in safeguards against flagging good candidates.
    
    This class provides:
    - Confidence scoring based on data quality and quantity
    - Uncertainty quantification for all metrics
    - Human override tracking and validation
    - Context-aware anomaly detection
    """
    
    def __init__(self):
        self.min_questions_for_confidence = 3
        self.min_questions_for_high_confidence = 5
        
    def calculate_assessment_confidence(
        self,
        metrics: Dict,
        per_task_metrics: List[Dict],
        behavioral_consistency: Dict,
        population_context: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate meta-confidence in our own analysis.
        
        Returns a confidence score (0-1) with detailed factors explaining
        why confidence is high, medium, or low.
        """
        factors = {}
        
        # Factor 1: Sample Size
        tasks_completed = len(per_task_metrics)
        if tasks_completed >= self.min_questions_for_high_confidence:
            factors["sample_size"] = {
                "score": 1.0,
                "reason": f"Sufficient data: {tasks_completed} questions analyzed",
                "weight": 0.25
            }
        elif tasks_completed >= self.min_questions_for_confidence:
            factors["sample_size"] = {
                "score": 0.6,
                "reason": f"Moderate data: {tasks_completed} questions (recommend 5+ for higher confidence)",
                "weight": 0.25
            }
        else:
            factors["sample_size"] = {
                "score": 0.3,
                "reason": f"Limited data: Only {tasks_completed} question(s) analyzed. Results are preliminary.",
                "weight": 0.25
            }
        
        # Factor 2: Data Quality (event coverage)
        event_coverage = self._calculate_event_coverage(per_task_metrics)
        factors["data_quality"] = {
            "score": event_coverage,
            "reason": f"Event coverage: {event_coverage:.0%} of expected events captured",
            "weight": 0.20
        }
        
        # Factor 3: Cross-Layer Agreement
        layer_agreement = self._check_layer_agreement(metrics, behavioral_consistency)
        factors["cross_layer_agreement"] = {
            "score": layer_agreement["score"],
            "reason": layer_agreement["reason"],
            "weight": 0.20
        }
        
        # Factor 4: Pattern Stability
        stability = self._calculate_pattern_stability(per_task_metrics)
        factors["pattern_stability"] = {
            "score": stability["score"],
            "reason": stability["reason"],
            "weight": 0.15
        }
        
        # Factor 5: Population Context Availability
        has_population = population_context is not None and len(population_context.get("percentiles", {})) > 0
        factors["population_context"] = {
            "score": 1.0 if has_population else 0.5,
            "reason": "Population baseline available for comparison" if has_population else "Limited population data for comparison",
            "weight": 0.10
        }
        
        # Factor 6: Behavioral Consistency Confidence
        consistency_confidence = behavioral_consistency.get("confidence_explanation", {}).get("level", "low")
        consistency_score = {"high": 1.0, "moderate": 0.7, "low": 0.4}.get(consistency_confidence, 0.4)
        factors["behavioral_consistency"] = {
            "score": consistency_score,
            "reason": f"Behavioral consistency analysis: {consistency_confidence} confidence",
            "weight": 0.10
        }
        
        # Calculate weighted overall confidence
        overall_confidence = sum(
            f["score"] * f["weight"] for f in factors.values()
        )
        
        # Determine confidence level and recommendation
        if overall_confidence >= 0.75:
            level = "high"
            recommendation = {
                "action": "proceed",
                "message": "High confidence assessment. Results are reliable based on sufficient data and consistent patterns.",
                "auto_flag": False
            }
        elif overall_confidence >= 0.50:
            level = "moderate"
            recommendation = {
                "action": "review_suggested",
                "message": "Moderate confidence. Consider human review for borderline cases.",
                "auto_flag": False
            }
        else:
            level = "low"
            recommendation = {
                "action": "insufficient_data",
                "message": "Low confidence due to limited data or high variability. Recommend additional assessment or human evaluation.",
                "auto_flag": False  # Never auto-flag low confidence assessments
            }
        
        return {
            "overall": round(overall_confidence, 2),
            "level": level,
            "factors": factors,
            "recommendation": recommendation,
            "interpretation": self._get_confidence_interpretation(overall_confidence, factors)
        }
    
    def _calculate_event_coverage(self, per_task_metrics: List[Dict]) -> float:
        """Calculate what percentage of expected events were captured."""
        if not per_task_metrics:
            return 0.0
        
        expected_events_per_task = 4  # task_started, option_selected, reasoning, task_completed
        total_expected = len(per_task_metrics) * expected_events_per_task
        
        # Count actual events (simplified - in practice would count from event log)
        completed_tasks = sum(1 for m in per_task_metrics if m.get("is_completed", False))
        actual_events = completed_tasks * expected_events_per_task
        
        return min(1.0, actual_events / max(total_expected, 1))
    
    def _check_layer_agreement(self, metrics: Dict, behavioral_consistency: Dict) -> Dict:
        """Check if different analysis layers agree with each other."""
        # Simplified check - in practice would compare multiple dimensions
        flags = behavioral_consistency.get("flags", [])
        high_severity_flags = sum(1 for f in flags if f.get("severity") == "high")
        
        if high_severity_flags == 0:
            return {
                "score": 1.0,
                "reason": "All analysis layers show consistent patterns"
            }
        elif high_severity_flags <= 2:
            return {
                "score": 0.7,
                "reason": f"{high_severity_flags} minor inconsistencies between layers"
            }
        else:
            return {
                "score": 0.4,
                "reason": f"{high_severity_flags} significant inconsistencies detected"
            }
    
    def _calculate_pattern_stability(self, per_task_metrics: List[Dict]) -> Dict:
        """Calculate how stable behavioral patterns are across tasks."""
        if len(per_task_metrics) < 2:
            return {
                "score": 0.5,
                "reason": "Insufficient data for stability analysis"
            }
        
        # Check timing stability
        times = [m.get("time_spent_seconds", 0) for m in per_task_metrics if m.get("time_spent_seconds")]
        if len(times) >= 2:
            try:
                cv = stdev(times) / mean(times)  # Coefficient of variation
                # Moderate variation is good (not too robotic, not too erratic)
                if 0.15 <= cv <= 0.60:
                    return {
                        "score": 1.0,
                        "reason": f"Stable patterns with healthy variation ({cv:.0%} coefficient of variation)"
                    }
                elif cv < 0.15:
                    return {
                        "score": 0.6,
                        "reason": f"Low variation ({cv:.0%}) - patterns may be overly consistent"
                    }
                else:
                    return {
                        "score": 0.7,
                        "reason": f"High variation ({cv:.0%}) - patterns are somewhat erratic"
                    }
            except:
                pass
        
        return {
            "score": 0.7,
            "reason": "Moderate pattern stability"
        }
    
    def _get_confidence_interpretation(self, confidence: float, factors: Dict) -> str:
        """Generate human-readable interpretation of confidence score."""
        if confidence >= 0.75:
            return (
                f"This assessment has high confidence ({confidence:.0%}) based on: "
                f"{factors['sample_size']['reason']}. "
                f"The results are reliable and can be used with confidence for hiring decisions."
            )
        elif confidence >= 0.50:
            low_factors = [k for k, v in factors.items() if v['score'] < 0.6]
            return (
                f"This assessment has moderate confidence ({confidence:.0%}). "
                f"Areas to consider: {', '.join(low_factors)}. "
                f"Results are informative but human judgment is recommended for borderline cases."
            )
        else:
            low_factors = [k for k, v in factors.items() if v['score'] < 0.6]
            return (
                f"This assessment has low confidence ({confidence:.0%}) due to: "
                f"{', '.join(low_factors)}. "
                f"Results are preliminary. Consider: (1) requesting additional assessment, "
                f"(2) conducting interview, or (3) reviewing raw behavioral data directly."
            )
    
    def generate_override_controls(self, assessment_id: str, current_grade: str) -> Dict:
        """
        Generate controls for human override of system recommendations.
        
        This ensures recruiters can always override the system and tracks
        when and why overrides occur for continuous improvement.
        """
        return {
            "can_override": True,
            "override_options": [
                {
                    "value": "upgrade",
                    "label": "Upgrade Grade",
                    "description": "Candidate performed better than grade suggests"
                },
                {
                    "value": "downgrade",
                    "label": "Downgrade Grade",
                    "description": "Candidate performed worse than grade suggests"
                },
                {
                    "value": "insufficient_data",
                    "label": "Insufficient Data",
                    "description": "Assessment doesn't capture candidate's abilities"
                },
                {
                    "value": "contextual_factors",
                    "label": "Contextual Factors",
                    "description": "External factors affected performance (e.g., technical issues)"
                }
            ],
            "requires_reason": True,
            "reason_min_length": 20,
            "current_grade": current_grade,
            "disclaimer": (
                "By overriding, you acknowledge that you have additional context "
                "not captured by this assessment. Your override will be logged for "
                "quality improvement purposes."
            )
        }
    
    def check_neurodiversity_considerations(self, per_task_metrics: List[Dict]) -> Dict:
        """
        Check for patterns that might indicate neurodivergent responding styles.
        
        This helps prevent false positives by flagging patterns that are
        consistent with (not suspicious) neurodivergent behavior.
        """
        considerations = []
        
        if not per_task_metrics:
            return {"considerations": considerations}
        
        # Check for consistent timing (may indicate preference for routine)
        times = [m.get("time_spent_seconds", 0) for m in per_task_metrics if m.get("time_spent_seconds")]
        if len(times) >= 3:
            try:
                cv = stdev(times) / mean(times)
                if cv < 0.15:
                    considerations.append({
                        "type": "consistent_timing",
                        "description": "Very consistent response times observed",
                        "possible_explanation": "May indicate preference for systematic approach or routine",
                        "recommendation": "Consider if consistent approach aligns with role requirements rather than flagging as suspicious"
                    })
            except:
                pass
        
        # Check for zero revisions (may indicate high confidence or decisiveness)
        changes = [m.get("decision_changes", 0) for m in per_task_metrics]
        if all(c == 0 for c in changes) and len(changes) >= 3:
            considerations.append({
                "type": "no_revisions",
                "description": "No answer revisions across all questions",
                "possible_explanation": "May indicate high confidence, expertise, or decisive decision-making style",
                "recommendation": "Review explanation quality. High-quality explanations with no revisions suggest expertise."
            })
        
        # Check for extended deliberation (may indicate thorough processing)
        avg_time = mean(times) if times else 0
        if avg_time > 45:
            considerations.append({
                "type": "extended_deliberation",
                "description": "Extended time spent on questions",
                "possible_explanation": "May indicate thorough processing, careful consideration, or need for additional processing time",
                "recommendation": "Consider if role requires quick decisions or thorough analysis. Extended time is not inherently negative."
            })
        
        return {
            "considerations": considerations,
            "has_neurodiversity_considerations": len(considerations) > 0,
            "note": (
                "These patterns may reflect neurodivergent cognitive styles or individual preferences. "
                "They should not be automatically flagged as suspicious. Consider context and role requirements."
            )
        }
    
    def validate_override(self, override_data: Dict) -> Tuple[bool, str]:
        """
        Validate an override request.
        
        Returns (is_valid, error_message)
        """
        if not override_data.get("reason"):
            return False, "Override reason is required"
        
        if len(override_data.get("reason", "")) < 20:
            return False, "Override reason must be at least 20 characters"
        
        if override_data.get("new_grade") not in ["S", "A", "B", "C", "D"]:
            return False, "Invalid grade. Must be S, A, B, C, or D"
        
        return True, ""


# Singleton instance
_false_positive_protection = None

def get_false_positive_protection() -> FalsePositiveProtection:
    """Get or create the FalsePositiveProtection singleton."""
    global _false_positive_protection
    if _false_positive_protection is None:
        _false_positive_protection = FalsePositiveProtection()
    return _false_positive_protection
