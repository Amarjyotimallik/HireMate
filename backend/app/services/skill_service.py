"""
Skill Service

Interprets computed metrics into human-readable skill profiles.
All interpretations are DETERMINISTIC and RULE-BASED.
"""

from datetime import datetime
from typing import Dict, Optional, List

from bson import ObjectId

from app.db import get_skills_collection, get_metrics_collection, get_attempts_collection
from app.schemas import (
    ComputedMetricsResponse,
    SkillProfileResponse,
    ThinkingStyle,
    DecisionPattern,
    RiskOrientation,
    CommunicationStyle,
    ThinkingStyleType,
    DecisionSpeed,
    DecisionConsistency,
    RiskOrientationType,
    ReasoningDepthType,
    LogicalStructureType,
    CandidateSkillSummary,
    CandidateListResponse,
)
from app.services.metrics_service import get_metrics, compute_metrics
from app.core import AttemptNotFoundError


# Current version of skill interpretation logic
SKILL_VERSION = "1.0.0"


async def generate_skill_profile(attempt_id: str) -> SkillProfileResponse:
    """
    Generate a skill profile from computed metrics.
    
    This is called AFTER metrics are computed.
    All interpretations are deterministic and explainable.
    """
    skills_coll = get_skills_collection()
    
    # Check if already generated
    existing = await skills_coll.find_one({"attempt_id": attempt_id})
    if existing:
        return _skill_doc_to_response(existing)
    
    # Get or compute metrics
    metrics = await get_metrics(attempt_id)
    if not metrics:
        metrics = await compute_metrics(attempt_id)
    
    # Generate each skill dimension
    thinking_style = _interpret_thinking_style(metrics)
    decision_pattern = _interpret_decision_pattern(metrics)
    risk_orientation = _interpret_risk_orientation(metrics)
    communication_style = _interpret_communication_style(metrics)
    
    # Generate summary
    overall_summary = _generate_summary(
        thinking_style, decision_pattern, risk_orientation, communication_style
    )
    
    # Identify strengths and considerations
    strengths, considerations = _identify_strengths_and_considerations(
        metrics, thinking_style, decision_pattern, risk_orientation, communication_style
    )
    
    # Store skill profile
    now = datetime.utcnow()
    skill_doc = {
        "attempt_id": attempt_id,
        "metrics_id": metrics.id,
        "generated_at": now,
        "version": SKILL_VERSION,
        "thinking_style": thinking_style.model_dump(),
        "decision_pattern": decision_pattern.model_dump(),
        "risk_orientation": risk_orientation.model_dump(),
        "communication_style": communication_style.model_dump(),
        "overall_summary": overall_summary,
        "strengths": strengths,
        "considerations": considerations,
    }
    
    result = await skills_coll.insert_one(skill_doc)
    skill_doc["_id"] = result.inserted_id
    
    return _skill_doc_to_response(skill_doc)


async def get_skill_profile(attempt_id: str) -> Optional[SkillProfileResponse]:
    """Get skill profile for an attempt."""
    skills_coll = get_skills_collection()
    
    skill = await skills_coll.find_one({"attempt_id": attempt_id})
    if not skill:
        return None
    
    return _skill_doc_to_response(skill)


def _interpret_thinking_style(metrics: ComputedMetricsResponse) -> ThinkingStyle:
    """
    Interpret approach pattern from metrics.
    
    Uses behavioral descriptions with uncertainty language.
    Does NOT claim personality traits - describes observable patterns only.
    
    Rules:
    - High idle time + high explanation detail → Deliberative approach
    - Low idle time + many changes → Iterative approach
    - Low idle time + few changes → Direct approach
    - Moderate everything → Balanced approach
    """
    if not metrics.per_task_metrics:
        return ThinkingStyle(
            primary=ThinkingStyleType.METHODICAL,
            confidence=0.5,
            evidence=["Insufficient data for behavioral analysis"],
        )
    
    num_tasks = len(metrics.per_task_metrics)
    avg_idle_time = metrics.global_metrics.hesitation_time_seconds / num_tasks  # Will rename in schema later
    avg_changes = sum(m.decision_change_count for m in metrics.per_task_metrics) / num_tasks
    reasoning_depth = sum(m.reasoning_depth_score for m in metrics.per_task_metrics) / num_tasks
    
    evidence = []
    
    if avg_idle_time > 30 and reasoning_depth > 0.6:
        style = ThinkingStyleType.ANALYTICAL  # Maps to "Deliberative" in behavioral terms
        confidence = min(0.9, 0.6 + (reasoning_depth * 0.3))
        evidence = [
            f"Observed extended consideration time (avg {avg_idle_time:.1f}s per task)",
            f"Detailed explanations provided ({reasoning_depth:.0%} detail score)",
            "Pattern suggests deliberative approach to this assessment",  # Uncertainty language
        ]
    elif avg_idle_time < 15 and avg_changes >= 2:
        style = ThinkingStyleType.EXPLORATORY  # Maps to "Iterative" in behavioral terms
        confidence = min(0.85, 0.6 + (avg_changes * 0.1))
        evidence = [
            f"Quick initial selections observed (avg {avg_idle_time:.1f}s)",
            f"Multiple selection changes (avg {avg_changes:.1f} per task)",
            "Pattern indicates iterative refinement approach",  # Uncertainty language
        ]
    elif avg_idle_time < 20 and avg_changes < 1:
        style = ThinkingStyleType.INTUITIVE  # Maps to "Direct" in behavioral terms
        confidence = 0.75
        evidence = [
            f"Rapid selection observed (avg {avg_idle_time:.1f}s)",
            f"Selections rarely revised ({avg_changes:.1f} changes per task)",
            "Pattern suggests direct commitment to choices",  # Uncertainty language
        ]
    else:
        style = ThinkingStyleType.METHODICAL  # Maps to "Balanced" in behavioral terms
        confidence = 0.7
        evidence = [
            f"Moderate pace observed (avg {avg_idle_time:.1f}s consideration time)",
            f"Some revisions made ({avg_changes:.1f} changes per task)",
            "Pattern indicates balanced approach",
        ]
    
    return ThinkingStyle(
        primary=style,
        confidence=round(confidence, 2),
        evidence=evidence,
    )


def _interpret_decision_pattern(metrics: ComputedMetricsResponse) -> DecisionPattern:
    """
    Interpret decision speed and consistency.
    """
    if not metrics.per_task_metrics:
        return DecisionPattern(
            speed=DecisionSpeed.MODERATE,
            consistency=DecisionConsistency.STEADY,
            confidence=0.5,
            evidence=["Insufficient data for analysis"],
        )
    
    num_tasks = len(metrics.per_task_metrics)
    decision_times = [m.first_decision_speed_seconds for m in metrics.per_task_metrics]
    avg_decision_time = sum(decision_times) / len(decision_times)
    
    evidence = []
    
    # Determine speed
    if avg_decision_time < 15:
        speed = DecisionSpeed.FAST
        evidence.append(f"Quick decisions (avg {avg_decision_time:.1f}s to first choice)")
    elif avg_decision_time > 45:
        speed = DecisionSpeed.DELIBERATE
        evidence.append(f"Careful decisions (avg {avg_decision_time:.1f}s to first choice)")
    else:
        speed = DecisionSpeed.MODERATE
        evidence.append(f"Balanced decision pace (avg {avg_decision_time:.1f}s to first choice)")
    
    # Determine consistency
    consistency_score = metrics.aggregated_patterns.decision_consistency
    
    if consistency_score > 0.7:
        consistency = DecisionConsistency.STEADY
        evidence.append("Consistent decision-making pace across tasks")
    elif consistency_score < 0.4:
        consistency = DecisionConsistency.VARIABLE
        evidence.append("Adapts pace based on task complexity")
    else:
        # Check if improving over time
        first_half = decision_times[:len(decision_times)//2]
        second_half = decision_times[len(decision_times)//2:]
        if first_half and second_half:
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            if second_avg < first_avg * 0.8:
                consistency = DecisionConsistency.IMPROVING
                evidence.append("Decision speed improved throughout assessment")
            else:
                consistency = DecisionConsistency.STEADY
                evidence.append("Maintained consistent approach")
        else:
            consistency = DecisionConsistency.STEADY
    
    confidence = min(0.85, 0.5 + (consistency_score * 0.3) + (0.1 * num_tasks / 10))
    
    return DecisionPattern(
        speed=speed,
        consistency=consistency,
        confidence=round(confidence, 2),
        evidence=evidence,
    )


def _interpret_risk_orientation(metrics: ComputedMetricsResponse) -> RiskOrientation:
    """
    Interpret risk-taking preference from option choices.
    """
    risk_pref = metrics.aggregated_patterns.risk_preference
    total = risk_pref.low_count + risk_pref.medium_count + risk_pref.high_count
    
    if total == 0:
        return RiskOrientation(
            preference=RiskOrientationType.BALANCED,
            confidence=0.5,
            evidence=["Insufficient data for analysis"],
        )
    
    evidence = []
    
    if risk_pref.dominant == "low":
        preference = RiskOrientationType.RISK_AVERSE
        confidence = risk_pref.low_count / total
        evidence = [
            f"Selected options tagged as lower-risk in {risk_pref.low_count} of {total} tasks",
            "Tended toward cautious options in this assessment",  # Behavioral description
            "Note: Risk tags reflect option design, not inherent risk levels",  # Transparency
        ]
    elif risk_pref.dominant == "high":
        preference = RiskOrientationType.RISK_TOLERANT
        confidence = risk_pref.high_count / total
        evidence = [
            f"Selected options tagged as higher-risk in {risk_pref.high_count} of {total} tasks",
            "Showed preference for bolder options in this assessment",  # Behavioral description
            "Note: Risk tags reflect option design, not inherent risk levels",  # Transparency
        ]
    else:
        preference = RiskOrientationType.BALANCED
        confidence = 0.6
        evidence = [
            "No strong preference for risk level observed",
            f"Distribution: low ({risk_pref.low_count}), medium ({risk_pref.medium_count}), high ({risk_pref.high_count})",
            "May indicate adaptive approach based on scenario context",  # Uncertainty language
        ]
    
    return RiskOrientation(
        preference=preference,
        confidence=round(min(confidence, 0.9), 2),
        evidence=evidence,
    )


def _interpret_communication_style(metrics: ComputedMetricsResponse) -> CommunicationStyle:
    """
    Interpret explanation style from text analysis.
    
    Uses behavioral descriptions - describes text patterns, not communication ability.
    """
    if not metrics.per_task_metrics:
        return CommunicationStyle(
            reasoning_depth=ReasoningDepthType.MODERATE,
            logical_structure=LogicalStructureType.INFORMAL,
            confidence=0.5,
            evidence=["Insufficient explanation text for analysis"],
        )
    
    num_tasks = len(metrics.per_task_metrics)
    avg_word_count = sum(m.reasoning_word_count for m in metrics.per_task_metrics) / num_tasks
    avg_connectors = sum(m.reasoning_logical_keywords_count for m in metrics.per_task_metrics) / num_tasks
    
    evidence = []
    
    # Explanation length (not "reasoning depth" - we can't measure actual reasoning quality)
    if avg_word_count > 50:
        depth = ReasoningDepthType.DETAILED
        evidence.append(f"Explanations were detailed (avg {avg_word_count:.0f} words)")
    elif avg_word_count > 25:
        depth = ReasoningDepthType.MODERATE
        evidence.append(f"Explanations were moderate length (avg {avg_word_count:.0f} words)")
    else:
        depth = ReasoningDepthType.BRIEF
        evidence.append(f"Explanations were concise (avg {avg_word_count:.0f} words)")
    
    # Connector usage (not "logical structure" - connectors don't prove logic is valid)
    if avg_connectors > 3:
        structure = LogicalStructureType.STRUCTURED
        evidence.append(f"Used transition words/connectors ({avg_connectors:.1f} per response)")
    elif avg_connectors > 1:
        structure = LogicalStructureType.SEMI_STRUCTURED
        evidence.append(f"Some connector usage observed ({avg_connectors:.1f} per response)")
    else:
        structure = LogicalStructureType.INFORMAL
        evidence.append("Direct explanation style without formal connectors")
    
    # Add disclaimer about text analysis limitations
    evidence.append("Note: Text analysis describes style, not reasoning validity")
    
    confidence = min(0.85, 0.5 + metrics.aggregated_patterns.reasoning_engagement * 0.4)
    
    return CommunicationStyle(
        reasoning_depth=depth,
        logical_structure=structure,
        confidence=round(confidence, 2),
        evidence=evidence,
    )


def _generate_summary(
    thinking_style: ThinkingStyle,
    decision_pattern: DecisionPattern,
    risk_orientation: RiskOrientation,
    communication_style: CommunicationStyle,
) -> str:
    """
    Generate a recruiter-friendly summary paragraph.
    
    Uses behavioral observations with uncertainty language.
    Explicitly avoids personality claims.
    """
    style = thinking_style.primary.value
    speed = decision_pattern.speed.value
    risk = risk_orientation.preference.value
    depth = communication_style.reasoning_depth.value
    
    # Build summary based on key dimensions - uses "observed", "suggests", "pattern indicates"
    templates = {
        ("analytical", "risk_averse"): 
            "Behavioral observations suggest a deliberative approach to this assessment. "
            "The candidate took extended time to consider options and tended toward lower-risk choices. "
            "Explanations were structured with attention to potential consequences. "
            "Note: These in-assessment patterns may not generalize to role performance.",
        
        ("analytical", "balanced"):
            "The candidate's behavior pattern suggests deliberate evaluation of options. "
            "Risk preferences were balanced across scenarios. "
            "Explanations tended to be structured and considered multiple factors. "
            "Note: Observations are specific to this assessment context.",
        
        ("analytical", "risk_tolerant"):
            "Observed pattern combines extended consideration time with preference for bolder options. "
            "The candidate deliberated before selecting higher-risk choices. "
            "Explanations were detailed even when choosing higher-stakes options. "
            "Note: Risk labels reflect option design in this assessment.",
        
        ("intuitive", "risk_averse"):
            "The candidate made quick initial selections while tending toward cautious options. "
            "Selections were maintained with minimal revision. "
            "Explanations were direct and focused on key points. "
            "Note: Quick selection may reflect familiarity with scenario type.",
        
        ("intuitive", "balanced"):
            "Observed pattern shows rapid selections with balanced risk distribution. "
            "The candidate committed to choices quickly and adapted risk approach by context. "
            "Explanations were clear and action-oriented. "
            "Note: Observations are limited to this assessment.",
        
        ("intuitive", "risk_tolerant"):
            "The candidate selected quickly and showed preference for bolder options. "
            "Selections were made rapidly with minimal revision. "
            "Explanations were direct and concise. "
            "Note: Patterns may reflect assessment-specific factors.",
        
        ("exploratory", "risk_averse"):
            "Observed behavior included exploration of multiple options before finalizing. "
            "Despite iterative approach, final choices tended toward lower-risk options. "
            "This pattern suggests thorough consideration balanced with caution. "
            "Note: Risk tags are assessment-specific.",
        
        ("exploratory", "balanced"):
            "The candidate explored options before committing, changing selections during tasks. "
            "Risk preference varied by scenario context. "
            "Pattern suggests iterative refinement approach. "
            "Note: Exploration behavior may vary in different contexts.",
        
        ("exploratory", "risk_tolerant"):
            "Observed behavior included active option exploration with preference for bolder choices. "
            "The candidate iterated through possibilities before selecting higher-risk options. "
            "Pattern may indicate comfort with ambiguity in this assessment. "
            "Note: Behavior is context-specific.",
        
        ("methodical", "risk_averse"):
            "The candidate showed a systematic approach with preference for cautious options. "
            "Progress through tasks was steady with thorough consideration. "
            "Explanations tended to address potential downsides. "
            "Note: Pattern is specific to this assessment.",
        
        ("methodical", "balanced"):
            "Observed pattern suggests balanced, systematic task completion. "
            "The candidate evaluated options without extreme risk preferences. "
            "Explanations were structured and practical in approach. "
            "Note: Observations are limited to assessment context.",
        
        ("methodical", "risk_tolerant"):
            "The candidate combined steady pacing with willingness to select bolder options. "
            "Tasks were completed systematically without avoiding higher-risk choices. "
            "Pattern suggests measured approach. "
            "Note: Risk labels are assessment-specific.",
    }
    
    key = (style, risk.replace("-", "_") if risk else "balanced")
    summary = templates.get(key)
    
    if not summary:
        summary = (
            f"Observed approach pattern: {style} with {speed} selection timing. "
            f"Risk preference: {risk.replace('_', '-')}. "
            f"Explanation style: {depth}. "
            "Note: Observations are specific to this assessment and may not generalize."
        )
    
    return summary


def _identify_strengths_and_considerations(
    metrics: ComputedMetricsResponse,
    thinking_style: ThinkingStyle,
    decision_pattern: DecisionPattern,
    risk_orientation: RiskOrientation,
    communication_style: CommunicationStyle,
) -> tuple:
    """Identify observed strengths and neutral considerations (behavioral, not personality)."""
    strengths = []
    considerations = []
    
    # Approach pattern observations (not personality strengths)
    if thinking_style.primary == ThinkingStyleType.ANALYTICAL:
        strengths.append("Took time to consider options thoroughly")
    elif thinking_style.primary == ThinkingStyleType.INTUITIVE:
        strengths.append("Made selections quickly and maintained them")
    elif thinking_style.primary == ThinkingStyleType.EXPLORATORY:
        strengths.append("Explored multiple alternatives before finalizing")
    else:
        strengths.append("Progressed through tasks systematically")
    
    # Decision pattern observations
    if decision_pattern.consistency == DecisionConsistency.STEADY:
        strengths.append("Maintained consistent pacing across tasks")
    elif decision_pattern.consistency == DecisionConsistency.IMPROVING:
        strengths.append("Selection speed improved over course of assessment")
    
    # Explanation style observations
    if communication_style.reasoning_depth == ReasoningDepthType.DETAILED:
        strengths.append("Provided detailed explanations for choices")
    if communication_style.logical_structure == LogicalStructureType.STRUCTURED:
        strengths.append("Used structured language with connectors")
    
    # Session observations
    if metrics.aggregated_patterns.attention_stability > 0.8:
        strengths.append("Strong focus and attention")
    
    # Considerations (neutral observations, not weaknesses)
    if thinking_style.primary == ThinkingStyleType.ANALYTICAL:
        considerations.append("May prefer additional time for complex decisions")
    elif thinking_style.primary == ThinkingStyleType.INTUITIVE:
        considerations.append("Works best with clear, time-bounded scenarios")
    
    if risk_orientation.preference == RiskOrientationType.RISK_AVERSE:
        considerations.append("Prefers established approaches over experimental ones")
    elif risk_orientation.preference == RiskOrientationType.RISK_TOLERANT:
        considerations.append("May pursue innovative solutions even with uncertainty")
    
    if decision_pattern.speed == DecisionSpeed.DELIBERATE:
        considerations.append("Takes measured approach to commitments")
    
    return strengths[:4], considerations[:3]  # Limit to reasonable numbers


async def get_candidates_with_skills(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[str] = None,
) -> CandidateListResponse:
    """Get list of candidates with skill summaries."""
    attempts = get_attempts_collection()
    skills_coll = get_skills_collection()
    
    # Get completed attempts, filtered by user if provided
    query = {"status": {"$in": ["completed", "locked"]}}
    if user_id:
        query["created_by"] = user_id
        
    total = await attempts.count_documents(query)
    
    skip = (page - 1) * page_size
    cursor = attempts.find(query).skip(skip).limit(page_size).sort("completed_at", -1)
    
    candidates = []
    async for attempt in cursor:
        attempt_id = str(attempt["_id"])
        
        # Get skill profile (optional now)
        skill = await skills_coll.find_one({"attempt_id": attempt_id})
        
        # Include all candidates, use defaults if no skill profile
        if skill:
            candidates.append(CandidateSkillSummary(
                attempt_id=attempt_id,
                candidate_name=attempt["candidate_info"]["name"],
                candidate_email=attempt["candidate_info"]["email"],
                position=attempt["candidate_info"]["position"],
                thinking_style=ThinkingStyleType(skill["thinking_style"]["primary"]),
                risk_orientation=RiskOrientationType(skill["risk_orientation"]["preference"]),
                decision_speed=DecisionSpeed(skill["decision_pattern"]["speed"]),
                overall_summary=skill["overall_summary"],
                completed_at=attempt.get("completed_at", attempt["created_at"]),
            ))
        else:
            # Include candidate with default values when skill profile not generated yet
            candidates.append(CandidateSkillSummary(
                attempt_id=attempt_id,
                candidate_name=attempt["candidate_info"]["name"],
                candidate_email=attempt["candidate_info"]["email"],
                position=attempt["candidate_info"]["position"],
                thinking_style=ThinkingStyleType.METHODICAL,  # Default
                risk_orientation=RiskOrientationType.BALANCED,  # Default
                decision_speed=DecisionSpeed.MODERATE,  # Default
                overall_summary="Assessment completed. View Live Assessment for detailed behavioral analysis.",
                completed_at=attempt.get("completed_at", attempt.get("created_at")),
            ))
    
    return CandidateListResponse(
        candidates=candidates,
        total=total,
        page=page,
        page_size=page_size,
    )


def _skill_doc_to_response(doc: Dict) -> SkillProfileResponse:
    """Convert MongoDB document to response schema."""
    return SkillProfileResponse(
        id=str(doc["_id"]),
        attempt_id=doc["attempt_id"],
        metrics_id=doc["metrics_id"],
        generated_at=doc["generated_at"],
        version=doc["version"],
        thinking_style=ThinkingStyle(**doc["thinking_style"]),
        decision_pattern=DecisionPattern(**doc["decision_pattern"]),
        risk_orientation=RiskOrientation(**doc["risk_orientation"]),
        communication_style=CommunicationStyle(**doc["communication_style"]),
        overall_summary=doc["overall_summary"],
        strengths=doc["strengths"],
        considerations=doc["considerations"],
    )
