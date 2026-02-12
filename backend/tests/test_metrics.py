"""
Tests for Metrics Computation

Validates that behavioral metrics are computed correctly.
"""

import pytest
from datetime import datetime, timedelta

from app.schemas import (
    EventType,
    RiskLevel,
    GlobalMetrics,
    PerTaskMetrics,
    AggregatedPatterns,
)
from app.utils import (
    count_words,
    count_logical_keywords,
    calculate_reasoning_depth,
    analyze_reasoning,
)


class TestReasoningAnalyzer:
    """Tests for the reasoning text analyzer."""

    def test_count_words_empty(self):
        """Empty text should return 0."""
        assert count_words("") == 0
        assert count_words("   ") == 0
        assert count_words(None) == 0

    def test_count_words_simple(self):
        """Simple word counting."""
        assert count_words("Hello world") == 2
        assert count_words("One two three four five") == 5

    def test_count_logical_keywords(self):
        """Test logical keyword detection."""
        text = "Because I think therefore it works. However, we must consider alternatives."
        count, score = count_logical_keywords(text)
        
        # Should find: because (1.0), therefore (1.5), however (1.2)
        assert count >= 3
        assert score >= 3.5

    def test_calculate_reasoning_depth_empty(self):
        """Empty text should return 0."""
        assert calculate_reasoning_depth("") == 0
        assert calculate_reasoning_depth("   ") == 0

    def test_calculate_reasoning_depth_basic(self):
        """Basic reasoning should have some depth."""
        text = "I chose this option because it seems safer."
        depth = calculate_reasoning_depth(text)
        assert 0 < depth < 0.5  # Basic reasoning

    def test_calculate_reasoning_depth_structured(self):
        """Structured reasoning should have higher depth."""
        text = """
        I chose this option because it provides the best balance.
        Firstly, it addresses the immediate issue. Secondly, it 
        considers long-term implications. Therefore, I believe 
        this is the optimal approach. However, I acknowledge there 
        are risks that need to be monitored.
        """
        depth = calculate_reasoning_depth(text)
        assert depth > 0.5  # Good structured reasoning

    def test_analyze_reasoning_full(self):
        """Test full reasoning analysis."""
        text = "I think this is the right choice because it balances risk and reward."
        analysis = analyze_reasoning(text)
        
        assert "word_count" in analysis
        assert "character_count" in analysis
        assert "keyword_count" in analysis
        assert "depth_score" in analysis
        assert analysis["word_count"] > 0


class TestMetricsComputation:
    """Tests for behavioral metrics computation logic."""

    def test_global_metrics_structure(self):
        """Validate GlobalMetrics structure."""
        metrics = GlobalMetrics(
            total_time_seconds=300.0,
            active_interaction_time_seconds=250.0,
            hesitation_time_seconds=50.0,
            total_tasks=10,
            tasks_completed=10,
            avg_time_per_task_seconds=30.0,
        )
        
        assert metrics.total_time_seconds == 300.0
        assert metrics.hesitation_time_seconds == 50.0
        assert metrics.avg_time_per_task_seconds == 30.0

    def test_per_task_metrics_structure(self):
        """Validate PerTaskMetrics structure."""
        metrics = PerTaskMetrics(
            task_id="task_123",
            time_spent_seconds=45.0,
            hesitation_seconds=5.0,
            first_decision_speed_seconds=5.0,
            decision_change_count=2,
            final_option_id="opt_1",
            final_option_risk_level=RiskLevel.MEDIUM,
            reasoning_depth_score=0.65,
            reasoning_word_count=35,
            reasoning_logical_keywords_count=3,
            idle_time_seconds=2.0,
            focus_loss_count=0,
        )
        
        assert metrics.decision_change_count == 2
        assert metrics.reasoning_depth_score == 0.65

    def test_risk_preference_calculation(self):
        """Test risk preference aggregation logic."""
        from app.schemas import RiskPreference
        
        risk_pref = RiskPreference(
            low_count=7,
            medium_count=2,
            high_count=1,
            dominant="low",
        )
        
        # 70% low choices should indicate risk averse
        total = risk_pref.low_count + risk_pref.medium_count + risk_pref.high_count
        low_ratio = risk_pref.low_count / total
        
        assert low_ratio == 0.7
        assert risk_pref.dominant == "low"

    def test_aggregated_patterns_structure(self):
        """Validate AggregatedPatterns structure."""
        from app.schemas import RiskPreference
        
        patterns = AggregatedPatterns(
            risk_preference=RiskPreference(
                low_count=5,
                medium_count=3,
                high_count=2,
                dominant="balanced",
            ),
            decision_consistency=0.75,
            reasoning_engagement=0.65,
            attention_stability=0.9,
        )
        
        assert patterns.decision_consistency == 0.75
        assert patterns.attention_stability == 0.9
