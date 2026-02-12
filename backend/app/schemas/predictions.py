"""
ML Predictions API schemas.
"""

from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field


class InterviewSuccessRequest(BaseModel):
    """Request for interview success prediction."""
    attempt_id: str = Field(..., min_length=1)
    include_resume: bool = Field(True, description="Blend in resume/ATS score if available")


class InterviewSuccessResponse(BaseModel):
    """Interview success probability response."""
    probability: float = Field(..., description="0-100")
    confidence: str = Field(..., description="high | medium | low")
    factors: List[Dict[str, Any]] = Field(default_factory=list)
    message: Optional[str] = None


class JobFitPredictRequest(BaseModel):
    """Request for job-fit prediction (predictions API)."""
    resume_text: str = Field(..., min_length=1)
    job_description: str = Field("")


class JobFitPredictResponse(BaseModel):
    """Job fit prediction response."""
    fit_score: float = Field(..., description="0-100")
    breakdown: Dict[str, float] = Field(default_factory=dict)
    suggestions: Optional[List[str]] = None


class BehavioralResponse(BaseModel):
    """Behavioral traits prediction response."""
    predicted_traits: List[str] = Field(default_factory=list)
    confidence: str = Field(..., description="high | medium | low")
    message: Optional[str] = None
