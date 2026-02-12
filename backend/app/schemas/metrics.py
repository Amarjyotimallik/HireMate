"""
Computed Metrics Pydantic Schemas
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.task import RiskLevel


class RiskPreference(BaseModel):
    """Risk preference aggregation."""
    low_count: int = 0
    medium_count: int = 0
    high_count: int = 0
    dominant: str = "balanced"  # low, medium, high, balanced


class GlobalMetrics(BaseModel):
    """Global metrics across all tasks."""
    total_time_seconds: float
    active_interaction_time_seconds: float
    hesitation_time_seconds: float
    total_tasks: int
    tasks_completed: int
    avg_time_per_task_seconds: float


class PerTaskMetrics(BaseModel):
    """Metrics for a single task."""
    task_id: str
    time_spent_seconds: float
    hesitation_seconds: float
    first_decision_speed_seconds: float
    decision_change_count: int
    final_option_id: str
    final_option_risk_level: RiskLevel
    reasoning_depth_score: float = Field(..., ge=0, le=1)
    reasoning_word_count: int
    reasoning_logical_keywords_count: int
    idle_time_seconds: float
    focus_loss_count: int


class AggregatedPatterns(BaseModel):
    """Aggregated behavioral patterns."""
    risk_preference: RiskPreference
    decision_consistency: float = Field(..., ge=0, le=1)
    reasoning_engagement: float = Field(..., ge=0, le=1)
    attention_stability: float = Field(..., ge=0, le=1)


class ComputedMetricsResponse(BaseModel):
    """Schema for computed metrics response."""
    id: str
    attempt_id: str
    computed_at: datetime
    version: str
    global_metrics: GlobalMetrics
    per_task_metrics: List[PerTaskMetrics]
    aggregated_patterns: AggregatedPatterns

    class Config:
        from_attributes = True


class MetricsComputeRequest(BaseModel):
    """Request to trigger metrics computation."""
    force_recompute: bool = False
