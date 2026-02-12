"""
Behavior Event Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of behavior events."""
    TASK_STARTED = "task_started"
    OPTION_VIEWED = "option_viewed"
    OPTION_SELECTED = "option_selected"
    OPTION_CHANGED = "option_changed"
    REASONING_STARTED = "reasoning_started"
    REASONING_UPDATED = "reasoning_updated"
    REASONING_SUBMITTED = "reasoning_submitted"
    TASK_COMPLETED = "task_completed"
    IDLE_DETECTED = "idle_detected"
    FOCUS_LOST = "focus_lost"
    FOCUS_GAINED = "focus_gained"
    TASK_SKIPPED = "task_skipped"      # Candidate skipped a question
    PASTE_DETECTED = "paste_detected"  # Anti-cheat: detect copy-paste
    COPY_DETECTED = "copy_detected"    # Anti-cheat: detect copying question


# Payload schemas for each event type
class TaskStartedPayload(BaseModel):
    """Payload for task_started event."""
    task_index: int = Field(..., ge=0)


class OptionViewedPayload(BaseModel):
    """Payload for option_viewed event."""
    option_id: str
    view_duration_ms: Optional[int] = Field(None, ge=0)


class OptionSelectedPayload(BaseModel):
    """Payload for option_selected event."""
    option_id: str
    is_first_selection: bool = True


class OptionChangedPayload(BaseModel):
    """Payload for option_changed event."""
    from_option_id: str
    to_option_id: str
    time_since_last_change_ms: int = Field(..., ge=0)


class ReasoningStartedPayload(BaseModel):
    """Payload for reasoning_started event."""
    time_since_task_start_ms: int = Field(..., ge=0)


class ReasoningUpdatedPayload(BaseModel):
    """Payload for reasoning_updated event."""
    character_count: int = Field(..., ge=0)
    word_count: int = Field(..., ge=0)


class ReasoningSubmittedPayload(BaseModel):
    """Payload for reasoning_submitted event."""
    final_text: str
    word_count: int = Field(..., ge=0)
    character_count: int = Field(..., ge=0)


class TaskCompletedPayload(BaseModel):
    """Payload for task_completed event."""
    final_option_id: str
    task_duration_ms: int = Field(..., ge=0)


class IdleDetectedPayload(BaseModel):
    """Payload for idle_detected event."""
    idle_duration_ms: int = Field(..., ge=0)
    last_activity_type: str


class FocusPayload(BaseModel):
    """Payload for focus_lost and focus_gained events."""
    trigger: str  # e.g., "tab_switch", "window_blur"


class PasteDetectedPayload(BaseModel):
    """Payload for paste_detected event (anti-cheat)."""
    char_count: int = Field(..., ge=0)
    source: str  # e.g., "reasoning", "option"


class CopyDetectedPayload(BaseModel):
    """Payload for copy_detected event (anti-cheat)."""
    text_preview: str  # First 50 chars of copied text
    char_count: int = Field(..., ge=0)
    source: str  # e.g., "question_text", "options"


class EventCreate(BaseModel):
    """Schema for creating a behavior event."""
    task_id: str
    event_type: EventType
    payload: Dict[str, Any]
    client_timestamp: Optional[datetime] = None


class EventBatchCreate(BaseModel):
    """Schema for batch event creation."""
    events: List[EventCreate] = Field(..., min_length=1, max_length=100)


class EventResponse(BaseModel):
    """Schema for event response."""
    id: str
    attempt_id: str
    task_id: str
    event_type: EventType
    timestamp: datetime
    sequence_number: int
    payload: Dict[str, Any]
    client_timestamp: Optional[datetime]

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Schema for event list response."""
    events: List[EventResponse]
    total: int


class WebSocketEvent(BaseModel):
    """Schema for WebSocket event message."""
    type: str = "event"
    event_type: EventType
    payload: Dict[str, Any]
    client_timestamp: Optional[str] = None


class WebSocketEventLogged(BaseModel):
    """Schema for WebSocket event confirmation."""
    type: str = "event_logged"
    event_id: str
    event_type: str
    timestamp: str
    payload: Dict[str, Any]


class WebSocketAttemptStatus(BaseModel):
    """Schema for WebSocket attempt status update."""
    type: str = "attempt_status"
    status: str
    current_task_index: int
    total_tasks: int


class WebSocketAssessmentCompleted(BaseModel):
    """Schema for WebSocket assessment completed message."""
    type: str = "assessment_completed"
    attempt_id: str
    completed_at: str
