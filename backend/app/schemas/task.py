"""
Task Pydantic Schemas
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class TaskCategory(str, Enum):
    """Task category types."""
    PROBLEM_SOLVING = "problem_solving"
    COMMUNICATION = "communication"
    DECISION_CONFIDENCE = "decision_confidence"
    ANALYTICAL_THINKING = "analytical_thinking"
    SPEED_ACCURACY = "speed_accuracy"


class TaskDifficulty(str, Enum):
    """Task difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class RiskLevel(str, Enum):
    """Risk level for options."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskOption(BaseModel):
    """Schema for a task option."""
    id: str = Field(..., description="Unique ID within task, e.g., 'opt_1'")
    text: str = Field(..., min_length=1, max_length=500)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    behavioral_tags: List[str] = Field(default_factory=list)


class TaskBase(BaseModel):
    """Base task schema."""
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    scenario: str = Field(..., min_length=10, max_length=2000)
    category: TaskCategory
    difficulty: TaskDifficulty
    time_limit_seconds: Optional[int] = Field(None, ge=30, le=1800)
    options: List[TaskOption] = Field(..., min_length=2, max_length=6)
    reasoning_required: bool = True
    reasoning_min_length: int = Field(20, ge=0, le=500)


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    scenario: Optional[str] = Field(None, min_length=10, max_length=2000)
    category: Optional[TaskCategory] = None
    difficulty: Optional[TaskDifficulty] = None
    time_limit_seconds: Optional[int] = Field(None, ge=30, le=1800)
    options: Optional[List[TaskOption]] = Field(None, min_length=2, max_length=6)
    reasoning_required: Optional[bool] = None
    reasoning_min_length: Optional[int] = Field(None, ge=0, le=500)
    is_active: Optional[bool] = None


class TaskResponse(TaskBase):
    """Schema for task response."""
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for paginated task list."""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskBrief(BaseModel):
    """Brief task info for assessment."""
    id: str
    title: str
    scenario: str
    category: TaskCategory
    difficulty: TaskDifficulty
    options: List[TaskOption]
    reasoning_required: bool
    reasoning_min_length: int
    time_limit_seconds: Optional[int]
