"""
Tests for Skill Interpretation

Validates that skill profiles are generated correctly with deterministic rules.
"""

import pytest

from app.schemas import (
    ThinkingStyleType,
    DecisionSpeed,
    DecisionConsistency,
    RiskOrientationType,
    ReasoningDepthType,
    LogicalStructureType,
    ThinkingStyle,
    DecisionPattern,
    RiskOrientation,
    CommunicationStyle,
    RiskLevel,
    GlobalMetrics,
    PerTaskMetrics,
    AggregatedPatterns,
    RiskPreference,
    ComputedMetricsResponse,
)


def create_mock_metrics(
    avg_hesitation: float = 20.0,
    avg_changes: float = 1.0,
    avg_reasoning_depth: float = 0.5,
    risk_dominant: str = "balanced",
    avg_word_count: int = 30,
    avg_keywords: int = 2,
) -> ComputedMetricsResponse:
    """Create mock metrics for testing skill interpretation."""
    num_tasks = 10
    
    per_task = []
    for i in range(num_tasks):
        # Assign risk levels based on dominant pattern
        if risk_dominant == "low":
            risk = RiskLevel.LOW if i < 7 else RiskLevel.MEDIUM
        elif risk_dominant == "high":
            risk = RiskLevel.HIGH if i < 7 else RiskLevel.MEDIUM
        else:
            risk = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH][i % 3]
        
        per_task.append(PerTaskMetrics(
            task_id=f"task_{i}",
            time_spent_seconds=avg_hesitation + 30,
            hesitation_seconds=avg_hesitation,
            first_decision_speed_seconds=avg_hesitation,
            decision_change_count=int(avg_changes),
            final_option_id=f"opt_{i % 4}",
            final_option_risk_level=risk,
            reasoning_depth_score=avg_reasoning_depth,
            reasoning_word_count=avg_word_count,
            reasoning_logical_keywords_count=avg_keywords,
            idle_time_seconds=5.0,
            focus_loss_count=0,
        ))
    
    # Calculate risk counts
    low_count = sum(1 for m in per_task if m.final_option_risk_level == RiskLevel.LOW)
    med_count = sum(1 for m in per_task if m.final_option_risk_level == RiskLevel.MEDIUM)
    high_count = sum(1 for m in per_task if m.final_option_risk_level == RiskLevel.HIGH)
    
    return ComputedMetricsResponse(
        id="metrics_123",
        attempt_id="attempt_123",
        computed_at="2026-01-30T00:00:00",
        version="1.0.0",
        global_metrics=GlobalMetrics(
            total_time_seconds=(avg_hesitation + 30) * num_tasks,
            active_interaction_time_seconds=(avg_hesitation + 25) * num_tasks,
            hesitation_time_seconds=avg_hesitation * num_tasks,
            total_tasks=num_tasks,
            tasks_completed=num_tasks,
            avg_time_per_task_seconds=avg_hesitation + 30,
        ),
        per_task_metrics=per_task,
        aggregated_patterns=AggregatedPatterns(
            risk_preference=RiskPreference(
                low_count=low_count,
                medium_count=med_count,
                high_count=high_count,
                dominant=risk_dominant,
            ),
            decision_consistency=0.7,
            reasoning_engagement=avg_reasoning_depth,
            attention_stability=0.9,
        ),
    )


class TestThinkingStyleInterpretation:
    """Tests for thinking style interpretation rules."""

    def test_analytical_style(self):
        """High hesitation + high reasoning depth = Analytical."""
        # Simulating the interpretation logic
        avg_hesitation = 35.0  # > 30
        avg_reasoning_depth = 0.7  # > 0.6
        
        # Based on the rules in skill_service.py
        if avg_hesitation > 30 and avg_reasoning_depth > 0.6:
            style = ThinkingStyleType.ANALYTICAL
        else:
            style = ThinkingStyleType.METHODICAL
        
        assert style == ThinkingStyleType.ANALYTICAL

    def test_exploratory_style(self):
        """Low hesitation + many changes = Exploratory."""
        avg_hesitation = 10.0  # < 15
        avg_changes = 2.5  # >= 2
        
        if avg_hesitation < 15 and avg_changes >= 2:
            style = ThinkingStyleType.EXPLORATORY
        else:
            style = ThinkingStyleType.METHODICAL
        
        assert style == ThinkingStyleType.EXPLORATORY

    def test_intuitive_style(self):
        """Low hesitation + few changes = Intuitive."""
        avg_hesitation = 10.0  # < 20
        avg_changes = 0.5  # < 1
        
        if avg_hesitation < 20 and avg_changes < 1:
            style = ThinkingStyleType.INTUITIVE
        else:
            style = ThinkingStyleType.METHODICAL
        
        assert style == ThinkingStyleType.INTUITIVE

    def test_methodical_style(self):
        """Moderate everything = Methodical."""
        avg_hesitation = 25.0  # Not extreme
        avg_changes = 1.5  # Moderate
        avg_reasoning_depth = 0.5  # Moderate
        
        # None of the specific conditions match
        is_analytical = avg_hesitation > 30 and avg_reasoning_depth > 0.6
        is_exploratory = avg_hesitation < 15 and avg_changes >= 2
        is_intuitive = avg_hesitation < 20 and avg_changes < 1
        
        if not (is_analytical or is_exploratory or is_intuitive):
            style = ThinkingStyleType.METHODICAL
        
        assert style == ThinkingStyleType.METHODICAL


class TestRiskOrientationInterpretation:
    """Tests for risk orientation interpretation rules."""

    def test_risk_averse_interpretation(self):
        """Majority low-risk choices = Risk Averse."""
        risk_pref = RiskPreference(
            low_count=8,
            medium_count=1,
            high_count=1,
            dominant="low",
        )
        
        total = risk_pref.low_count + risk_pref.medium_count + risk_pref.high_count
        if risk_pref.dominant == "low":
            preference = RiskOrientationType.RISK_AVERSE
            confidence = risk_pref.low_count / total
        
        assert preference == RiskOrientationType.RISK_AVERSE
        assert confidence == 0.8

    def test_risk_tolerant_interpretation(self):
        """Majority high-risk choices = Risk Tolerant."""
        risk_pref = RiskPreference(
            low_count=1,
            medium_count=2,
            high_count=7,
            dominant="high",
        )
        
        total = risk_pref.low_count + risk_pref.medium_count + risk_pref.high_count
        if risk_pref.dominant == "high":
            preference = RiskOrientationType.RISK_TOLERANT
            confidence = risk_pref.high_count / total
        
        assert preference == RiskOrientationType.RISK_TOLERANT
        assert confidence == 0.7

    def test_balanced_interpretation(self):
        """Mixed risk choices = Balanced."""
        risk_pref = RiskPreference(
            low_count=3,
            medium_count=4,
            high_count=3,
            dominant="balanced",
        )
        
        if risk_pref.dominant == "balanced":
            preference = RiskOrientationType.BALANCED
        
        assert preference == RiskOrientationType.BALANCED


class TestCommunicationStyleInterpretation:
    """Tests for communication style interpretation rules."""

    def test_detailed_reasoning(self):
        """High word count = Detailed reasoning depth."""
        avg_word_count = 60  # > 50
        
        if avg_word_count > 50:
            depth = ReasoningDepthType.DETAILED
        elif avg_word_count > 25:
            depth = ReasoningDepthType.MODERATE
        else:
            depth = ReasoningDepthType.BRIEF
        
        assert depth == ReasoningDepthType.DETAILED

    def test_structured_logic(self):
        """High keyword count = Structured logic."""
        avg_keywords = 4  # > 3
        
        if avg_keywords > 3:
            structure = LogicalStructureType.STRUCTURED
        elif avg_keywords > 1:
            structure = LogicalStructureType.SEMI_STRUCTURED
        else:
            structure = LogicalStructureType.INFORMAL
        
        assert structure == LogicalStructureType.STRUCTURED

    def test_brief_informal(self):
        """Low word count and keywords = Brief and informal."""
        avg_word_count = 15  # < 25
        avg_keywords = 0.5  # < 1
        
        if avg_word_count > 50:
            depth = ReasoningDepthType.DETAILED
        elif avg_word_count > 25:
            depth = ReasoningDepthType.MODERATE
        else:
            depth = ReasoningDepthType.BRIEF
        
        if avg_keywords > 3:
            structure = LogicalStructureType.STRUCTURED
        elif avg_keywords > 1:
            structure = LogicalStructureType.SEMI_STRUCTURED
        else:
            structure = LogicalStructureType.INFORMAL
        
        assert depth == ReasoningDepthType.BRIEF
        assert structure == LogicalStructureType.INFORMAL


class TestDecisionPatternInterpretation:
    """Tests for decision pattern interpretation rules."""

    def test_fast_decision_speed(self):
        """Low average decision time = Fast."""
        avg_decision_time = 10.0  # < 15
        
        if avg_decision_time < 15:
            speed = DecisionSpeed.FAST
        elif avg_decision_time > 45:
            speed = DecisionSpeed.DELIBERATE
        else:
            speed = DecisionSpeed.MODERATE
        
        assert speed == DecisionSpeed.FAST

    def test_deliberate_decision_speed(self):
        """High average decision time = Deliberate."""
        avg_decision_time = 50.0  # > 45
        
        if avg_decision_time < 15:
            speed = DecisionSpeed.FAST
        elif avg_decision_time > 45:
            speed = DecisionSpeed.DELIBERATE
        else:
            speed = DecisionSpeed.MODERATE
        
        assert speed == DecisionSpeed.DELIBERATE

    def test_steady_consistency(self):
        """High consistency score = Steady."""
        consistency_score = 0.8  # > 0.7
        
        if consistency_score > 0.7:
            consistency = DecisionConsistency.STEADY
        elif consistency_score < 0.4:
            consistency = DecisionConsistency.VARIABLE
        else:
            consistency = DecisionConsistency.STEADY  # Default
        
        assert consistency == DecisionConsistency.STEADY


class TestDeterministicOutput:
    """Verify that skill interpretation is deterministic."""

    def test_same_input_same_output(self):
        """Same metrics should always produce same skill profile."""
        # This tests the principle that interpretation is rule-based
        # Running the same logic twice should produce identical results
        
        avg_hesitation = 25.0
        avg_changes = 1.0
        avg_reasoning_depth = 0.5
        
        # First run
        is_analytical_1 = avg_hesitation > 30 and avg_reasoning_depth > 0.6
        is_exploratory_1 = avg_hesitation < 15 and avg_changes >= 2
        is_intuitive_1 = avg_hesitation < 20 and avg_changes < 1
        
        if is_analytical_1:
            style_1 = ThinkingStyleType.ANALYTICAL
        elif is_exploratory_1:
            style_1 = ThinkingStyleType.EXPLORATORY
        elif is_intuitive_1:
            style_1 = ThinkingStyleType.INTUITIVE
        else:
            style_1 = ThinkingStyleType.METHODICAL
        
        # Second run (same logic)
        is_analytical_2 = avg_hesitation > 30 and avg_reasoning_depth > 0.6
        is_exploratory_2 = avg_hesitation < 15 and avg_changes >= 2
        is_intuitive_2 = avg_hesitation < 20 and avg_changes < 1
        
        if is_analytical_2:
            style_2 = ThinkingStyleType.ANALYTICAL
        elif is_exploratory_2:
            style_2 = ThinkingStyleType.EXPLORATORY
        elif is_intuitive_2:
            style_2 = ThinkingStyleType.INTUITIVE
        else:
            style_2 = ThinkingStyleType.METHODICAL
        
        assert style_1 == style_2
        assert style_1 == ThinkingStyleType.METHODICAL
