"""
Score Fusion Service

Combines rule-based analysis (keyword depth) with AI semantic analysis
to produce enhanced, more accurate metrics.
"""

import logging
from typing import Dict, List, Optional
from app.utils.reasoning_analyzer import (
    analyze_reasoning,
    calculate_reasoning_depth,
    count_logical_keywords
)
from app.services.ai_analyzer import analyze_answer_with_ai

logger = logging.getLogger(__name__)


# Hedging words that indicate low confidence
HEDGING_WORDS = {
    "maybe", "perhaps", "possibly", "might", "could be", 
    "i think", "i guess", "not sure", "probably", "seems like",
    "kind of", "sort of", "apparently", "supposedly"
}

# Confident words that indicate high confidence
CONFIDENT_WORDS = {
    "definitely", "certainly", "clearly", "obviously", "must be",
    "absolutely", "without doubt", "for sure", "undoubtedly",
    "i know", "i'm certain", "this is because"
}


def detect_hedging(text: str) -> float:
    """
    Detect hedging language in text.
    
    Returns:
        Float 0-1 where higher = more hedging (less confident)
    """
    if not text:
        return 0.5
    
    text_lower = text.lower()
    
    hedging_count = sum(1 for word in HEDGING_WORDS if word in text_lower)
    confident_count = sum(1 for word in CONFIDENT_WORDS if word in text_lower)
    
    # Net hedging score
    total = hedging_count + confident_count
    if total == 0:
        return 0.5  # Neutral
    
    # Returns 0 (very confident) to 1 (very hedging)
    hedging_ratio = hedging_count / total
    return round(hedging_ratio, 2)


def calculate_hybrid_scores(
    question_text: str,
    selected_option: str,
    reasoning_text: str,
    skills_to_track: List[str],
    is_correct: bool = None,
    use_ai: bool = False
) -> Dict:
    """
    Calculate hybrid scores combining rule-based and AI analysis.
    
    Args:
        question_text: The question text
        selected_option: What the candidate selected
        reasoning_text: Candidate's reasoning
        skills_to_track: Skills to evaluate
        is_correct: Whether the answer is correct
        use_ai: Whether to use AI analysis (set False for faster testing)
    
    Returns:
        Dict with fused metrics:
            - skill_scores: { skill: 0-100 }
            - analytical_score: 0-100
            - confidence_score: 0-100
            - depth_score: 0-100
            - correctness_score: 0-100
            - overall_quality: 0-100
    """
    # Step 1: Rule-based analysis
    rule_analysis = analyze_reasoning(reasoning_text or "")
    depth_score = rule_analysis["depth_score"]  # 0-1
    keyword_count = rule_analysis["keyword_count"]
    word_count = rule_analysis["word_count"]
    
    # Step 2: Hedging detection
    hedging_level = detect_hedging(reasoning_text or "")
    rule_confidence = 1.0 - hedging_level  # Invert: less hedging = more confident
    
    # Step 3: AI analysis (if enabled)
    if use_ai:
        ai_analysis = analyze_answer_with_ai(
            question_text=question_text,
            selected_option=selected_option,
            reasoning_text=reasoning_text,
            skills_to_track=skills_to_track,
            is_correct=is_correct
        )
    else:
        # Fallback to rule-based only
        ai_analysis = {
            "skill_scores": {skill: 50 for skill in skills_to_track},
            "correctness": 0.5 if is_correct is None else (1.0 if is_correct else 0.0),
            "analytical_quality": depth_score,
            "confidence_level": rule_confidence,
            "relevance": 0.7
        }
    
    # Step 4: Score Fusion
    # Skill scores: 70% AI + 30% rule-based depth bonus
    fused_skill_scores = {}
    for skill in skills_to_track:
        ai_score = ai_analysis["skill_scores"].get(skill, 50)
        
        # Add bonus for good reasoning structure
        depth_bonus = 0
        if depth_score > 0.5:
            depth_bonus = (depth_score - 0.5) * 20  # Up to +10 bonus
        
        # Combine
        fused_score = (ai_score * 0.85) + (depth_score * 100 * 0.15) + depth_bonus
        fused_skill_scores[skill] = max(0, min(100, int(fused_score)))
    
    # Analytical score: 60% AI + 40% rule-based
    fused_analytical = (ai_analysis["analytical_quality"] * 0.6) + (depth_score * 0.4)
    
    # Confidence score: 50% AI + 50% hedging detection
    fused_confidence = (ai_analysis["confidence_level"] * 0.5) + (rule_confidence * 0.5)
    
    # Correctness: primarily AI (100%)
    correctness = ai_analysis["correctness"]
    
    # Overall quality: weighted average
    overall_quality = (
        correctness * 0.35 +           # Correctness matters most
        fused_analytical * 0.25 +       # Good reasoning
        ai_analysis["relevance"] * 0.2 + # Staying on topic
        fused_confidence * 0.2          # Confidence in answers
    )
    
    # Apply bonus if both rule-based AND AI agree on quality
    if depth_score > 0.5 and correctness > 0.7:
        overall_quality *= 1.10  # 10% bonus for well-explained correct answers
    
    return {
        "skill_scores": fused_skill_scores,
        "analytical_score": int(fused_analytical * 100),
        "confidence_score": int(fused_confidence * 100),
        "depth_score": int(depth_score * 100),
        "correctness_score": int(correctness * 100),
        "overall_quality": int(min(100, overall_quality * 100)),
        
        # Raw metrics for debugging/display
        "raw": {
            "rule_depth": depth_score,
            "rule_confidence": rule_confidence,
            "keyword_count": keyword_count,
            "word_count": word_count,
            "hedging_level": hedging_level,
            "ai_correctness": ai_analysis["correctness"],
            "ai_analytical": ai_analysis["analytical_quality"],
            "ai_confidence": ai_analysis["confidence_level"],
            "ai_relevance": ai_analysis["relevance"]
        }
    }


class CumulativeSkillTracker:
    """
    Tracks skill scores across multiple answers and calculates running averages.
    """
    
    def __init__(self, skills: List[str]):
        self.skills = skills
        self.skill_history: Dict[str, List[int]] = {skill: [] for skill in skills}
        self.answer_count = 0
    
    def add_answer(self, skill_scores: Dict[str, int]):
        """Add scores from a new answer."""
        self.answer_count += 1
        for skill, score in skill_scores.items():
            if skill in self.skill_history:
                self.skill_history[skill].append(score)
    
    def get_cumulative_scores(self) -> Dict[str, int]:
        """Get running average scores for each skill."""
        cumulative = {}
        for skill, history in self.skill_history.items():
            if history:
                # Weighted average: recent answers count more
                weights = [1 + (i * 0.2) for i in range(len(history))]
                weighted_sum = sum(s * w for s, w in zip(history, weights))
                total_weight = sum(weights)
                cumulative[skill] = int(weighted_sum / total_weight)
            else:
                cumulative[skill] = 0
        return cumulative
    
    def get_skill_trend(self, skill: str) -> str:
        """Get trend for a skill: 'improving', 'declining', or 'stable'."""
        history = self.skill_history.get(skill, [])
        if len(history) < 2:
            return "stable"
        
        # Compare last 2 scores
        recent = history[-2:]
        if recent[-1] > recent[-2] + 5:
            return "improving"
        elif recent[-1] < recent[-2] - 5:
            return "declining"
        return "stable"
    
    def to_dict(self) -> Dict:
        """Export tracker state."""
        return {
            "skills": self.get_cumulative_scores(),
            "answer_count": self.answer_count,
            "trends": {skill: self.get_skill_trend(skill) for skill in self.skills}
        }
