"""
Bulk Assessment Schemas

Pydantic models for bulk resume upload, job tracking, and results.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class BulkJobStatus(str, Enum):
    """Status of a bulk processing job."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BulkResultStatus(str, Enum):
    """Status of an individual file result within a bulk job."""
    SUCCESS = "success"
    FAILED = "failed"
    PROCESSING = "processing"
    SKIPPED = "skipped"


class BulkFileResult(BaseModel):
    """Result for a single file in a bulk job."""
    filename: str
    file_size: int = 0
    status: BulkResultStatus = BulkResultStatus.PROCESSING
    assessment_id: Optional[str] = None
    assessment_token: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    position: Optional[str] = None
    parsed_skills: List[str] = []
    error_message: Optional[str] = None
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class BulkJobResponse(BaseModel):
    """Response when creating a bulk job."""
    job_id: str
    status: BulkJobStatus = BulkJobStatus.QUEUED
    total_files: int = 0
    message: str = "Bulk processing job created"


class BulkJobStatusResponse(BaseModel):
    """Full status of a bulk job including results."""
    job_id: str
    status: BulkJobStatus
    total_files: int = 0
    processed_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    current_file: Optional[str] = None
    results: List[BulkFileResult] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BulkEmailRequest(BaseModel):
    """Request to send emails to multiple candidates."""
    assessment_ids: List[str] = Field(..., min_length=1)
    custom_message: Optional[str] = None


class BulkEmailResultItem(BaseModel):
    """Result of sending an email for a single assessment."""
    assessment_id: str
    status: str  # "success" or "failed"
    error: Optional[str] = None


class BulkEmailResponse(BaseModel):
    """Response from bulk email sending."""
    total: int
    success_count: int
    failed_count: int
    results: List[BulkEmailResultItem] = []


class BulkJobListResponse(BaseModel):
    """List of bulk jobs for the recruiter."""
    jobs: List[BulkJobStatusResponse] = []
    total: int = 0
