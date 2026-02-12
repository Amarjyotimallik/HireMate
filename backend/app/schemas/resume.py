"""
Resume / Document Upload Pydantic Schemas
"""

from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field


# ----- ATS & ML Predictions -----


class ATSScoreResponse(BaseModel):
    """Response for ATS score (resume vs job description)."""
    ats_score: float = Field(..., description="Overall ATS score 0-100")
    breakdown: Dict[str, float] = Field(default_factory=dict, description="Keywords, formatting, sections, etc.")
    formatting_issues: List[Dict[str, str]] = Field(default_factory=list)
    message: Optional[str] = Field(None, description="e.g. No resume text when score is 0")


class JobFitRequest(BaseModel):
    """Request body for job-fit and ATS score (raw text)."""
    resume_text: str = Field(..., min_length=1)
    job_description: str = Field("", description="Optional JD for job-fit; empty for formatting-only score")


class JobFitResponse(BaseModel):
    """Job fit score with breakdown (same as ATS + optional suggestions)."""
    fit_score: float = Field(..., description="0-100")
    breakdown: Dict[str, float] = Field(default_factory=dict)
    suggestions: Optional[List[str]] = None


class ResumeSuggestionsRequest(BaseModel):
    """Request for resume suggestions."""
    resume_text: str = Field(..., min_length=1)
    job_description: Optional[str] = Field(None)
    suggestion_types: Optional[List[str]] = Field(
        None,
        description="One or more of: keywords, formatting, skills, content. Default: all",
    )


class ResumeSuggestionsResponse(BaseModel):
    """Response from resume suggestions (flexible dict for hackathon)."""
    keyword_suggestions: Optional[Dict[str, Any]] = None
    formatting_suggestions: Optional[Dict[str, Any]] = None
    skills_analysis: Optional[Dict[str, Any]] = None
    content_suggestions: Optional[Dict[str, Any]] = None
    overall_score: float = 0.0


class BatchAtsRequest(BaseModel):
    """Batch ATS score: multiple resumes vs one JD."""
    resume_texts: List[str] = Field(..., min_length=1, max_length=100)
    job_description: str = Field("")


class BatchAtsItemResponse(BaseModel):
    """Single ATS result in batch."""
    index: int = 0
    ats_score: float = 0.0
    breakdown: Dict[str, float] = Field(default_factory=dict)


class BatchAtsResponse(BaseModel):
    """Batch ATS scores."""
    results: List[BatchAtsItemResponse] = Field(default_factory=list)


class BatchSuggestionsItemRequest(BaseModel):
    """Single item for batch suggestions."""
    resume_text: str = Field(..., min_length=1)
    job_description: Optional[str] = None


class BatchSuggestionsRequest(BaseModel):
    """Batch resume suggestions."""
    items: List[BatchSuggestionsItemRequest] = Field(..., min_length=1, max_length=50)


class BatchSuggestionsResponse(BaseModel):
    """Batch suggestions results."""
    results: List[ResumeSuggestionsResponse] = Field(default_factory=list)


# ----- Parse / Upload -----


class CandidateInfoExtracted(BaseModel):
    """Extracted candidate info from resume (all optional for pre-fill)."""
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    skills: List[str] = []
    resume_text: Optional[str] = None


class ResumeParseResponse(BaseModel):
    """Response after uploading and parsing a resume document."""
    candidate_info: CandidateInfoExtracted
    resume_url: Optional[str] = Field(None, description="URL or path to stored file if saved")
    resume_text: Optional[str] = None
    suggested_task_ids: Optional[List[str]] = Field(
        None,
        description="Task IDs suggested from parsed position so questions relate to the resume",
    )
