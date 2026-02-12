"""
Task Attempt Pydantic Schemas
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class AttemptStatus(str, Enum):
    """Status of an assessment attempt."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    LOCKED = "locked"


class CandidateInfo(BaseModel):
    """Candidate information for an attempt."""
    name: str = Field("Candidate", min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    position: str = Field("General Application", min_length=2, max_length=100)
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None
    skills: List[str] = []
    
    def __init__(self, **data):
        # Pre-process data before Pydantic validation
        if not data.get('name') or len(str(data.get('name', '')).strip()) < 2:
            data['name'] = 'Candidate'
        # Position is now extracted from resume; only default if truly missing/empty
        if not data.get('position') or len(str(data.get('position', '')).strip()) < 2:
            data['position'] = 'General Application'
        super().__init__(**data)


class AttemptCreate(BaseModel):
    """Schema for creating a new assessment attempt."""
    candidate_info: CandidateInfo
    task_ids: List[str] = Field(default_factory=list)
    expires_in_days: int = Field(7, ge=1, le=30)


class AttemptResponse(BaseModel):
    """Schema for attempt response."""
    id: str
    token: str
    candidate_info: CandidateInfo
    task_ids: List[str]
    status: AttemptStatus
    created_by: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: datetime
    current_task_index: int
    created_at: datetime
    analysis_result: Optional[dict] = None

    class Config:
        from_attributes = True


class AttemptBrief(BaseModel):
    """Brief attempt info for lists."""
    id: str
    candidate_name: str
    candidate_email: str
    position: str
    status: AttemptStatus
    total_tasks: int
    current_task_index: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    overall_score: Optional[float] = None
    overall_grade: Optional[str] = None


class AttemptListResponse(BaseModel):
    """Schema for paginated attempt list."""
    attempts: List[AttemptBrief]
    total: int
    page: int
    page_size: int


class AssessmentInfo(BaseModel):
    """Schema for assessment info (candidate view)."""
    attempt_id: str
    candidate_name: str
    position: str
    total_tasks: int
    current_task_index: int
    status: AttemptStatus
    expires_at: datetime


class AttemptStart(BaseModel):
    """Response when starting an assessment."""
    attempt_id: str
    message: str
    total_tasks: int
