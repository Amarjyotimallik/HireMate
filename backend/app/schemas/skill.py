"""
Skill Profile Pydantic Schemas
"""

from datetime import datetime
from typing import List
from enum import Enum

from pydantic import BaseModel, Field


class ThinkingStyleType(str, Enum):
    """Thinking style categories."""
    ANALYTICAL = "analytical"
    INTUITIVE = "intuitive"
    EXPLORATORY = "exploratory"
    METHODICAL = "methodical"


class DecisionSpeed(str, Enum):
    """Decision speed categories."""
    FAST = "fast"
    MODERATE = "moderate"
    DELIBERATE = "deliberate"


class DecisionConsistency(str, Enum):
    """Decision consistency categories."""
    STEADY = "steady"
    VARIABLE = "variable"
    IMPROVING = "improving"


class RiskOrientationType(str, Enum):
    """Risk orientation categories."""
    RISK_AVERSE = "risk_averse"
    BALANCED = "balanced"
    RISK_TOLERANT = "risk_tolerant"


class ReasoningDepthType(str, Enum):
    """Reasoning depth categories."""
    BRIEF = "brief"
    MODERATE = "moderate"
    DETAILED = "detailed"


class LogicalStructureType(str, Enum):
    """Logical structure categories."""
    INFORMAL = "informal"
    SEMI_STRUCTURED = "semi_structured"
    STRUCTURED = "structured"


class SkillDimension(BaseModel):
    """Base schema for a skill dimension with confidence."""
    confidence: float = Field(..., ge=0, le=1)
    evidence: List[str] = Field(default_factory=list)


class ThinkingStyle(SkillDimension):
    """Thinking style interpretation."""
    primary: ThinkingStyleType


class DecisionPattern(SkillDimension):
    """Decision pattern interpretation."""
    speed: DecisionSpeed
    consistency: DecisionConsistency


class RiskOrientation(SkillDimension):
    """Risk orientation interpretation."""
    preference: RiskOrientationType


class CommunicationStyle(SkillDimension):
    """Communication style interpretation."""
    reasoning_depth: ReasoningDepthType
    logical_structure: LogicalStructureType


class SkillProfileResponse(BaseModel):
    """Schema for skill profile response."""
    id: str
    attempt_id: str
    metrics_id: str
    generated_at: datetime
    version: str
    thinking_style: ThinkingStyle
    decision_pattern: DecisionPattern
    risk_orientation: RiskOrientation
    communication_style: CommunicationStyle
    overall_summary: str
    strengths: List[str]
    considerations: List[str]  # Neutral observations, not weaknesses

    class Config:
        from_attributes = True


class CandidateSkillSummary(BaseModel):
    """Brief skill summary for candidate lists."""
    attempt_id: str
    candidate_name: str
    candidate_email: str
    position: str
    thinking_style: ThinkingStyleType
    risk_orientation: RiskOrientationType
    decision_speed: DecisionSpeed
    overall_summary: str
    completed_at: datetime


class CandidateListResponse(BaseModel):
    """Paginated candidate list with skill summaries."""
    candidates: List[CandidateSkillSummary]
    total: int
    page: int
    page_size: int


class CandidateCompareRequest(BaseModel):
    """Request to compare candidates."""
    attempt_ids: List[str] = Field(..., min_length=2, max_length=5)


class CandidateCompareResponse(BaseModel):
    """Response with compared candidates."""
    candidates: List[SkillProfileResponse]
