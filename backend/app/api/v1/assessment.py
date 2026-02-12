"""
Assessment API Endpoints (Candidate-Facing)

These endpoints are authenticated via one-time assessment tokens,
not JWT tokens.
"""

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.schemas import AssessmentInfo, AttemptStart, TaskBrief, EventType, EventCreate
from app.services import (
    validate_and_get_assessment,
    start_assessment,
    complete_assessment,
    get_attempt_by_token,
    get_tasks_by_ids,
    update_task_progress,
    extend_attempt_expiry,
    log_event,
)
from app.core import (
    InvalidTokenError,
    TokenAlreadyUsedError,
    AttemptExpiredError,
    AttemptLockedError,
    AttemptNotFoundError,
)


router = APIRouter(prefix="/assessment", tags=["Assessment"])


@router.get("/{token}", response_model=AssessmentInfo)
async def validate_assessment(token: str):
    """
    Validate assessment token and get assessment info.
    
    This is the first call a candidate makes to verify their token is valid.
    """
    try:
        info = await validate_and_get_assessment(token)
        return info
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid assessment token",
        )
    except AttemptExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Assessment has expired",
        )
    except AttemptLockedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assessment has already been completed",
        )


@router.post("/{token}/start", response_model=AttemptStart)
async def start_assessment_endpoint(token: str):
    """
    Start the assessment.
    
    This consumes the one-time token (transitions from 'pending' to 'in_progress').
    If already in progress, allows resuming.
    """
    try:
        result = await start_assessment(token)
        return AttemptStart(**result)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid assessment token",
        )
    except TokenAlreadyUsedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assessment token has already been used",
        )
    except AttemptExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Assessment has expired",
        )


@router.get("/{token}/task/{task_index}", response_model=TaskBrief)
async def get_assessment_task(token: str, task_index: int):
    """
    Get a specific task for the assessment.
    
    Task index is 0-based.
    """
    attempt = await get_attempt_by_token(token)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid assessment token",
        )
    
    if attempt.status.value not in ["pending", "in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assessment is not active",
        )
    
    if task_index < 0 or task_index >= len(attempt.task_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task index out of range",
        )
    
    # Get the specific task
    task_id = attempt.task_ids[task_index]
    tasks = await get_tasks_by_ids([task_id])
    
    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Update progress
    await update_task_progress(attempt.id, task_index)
    
    # Extend session expiry on activity (keeps token alive)
    await extend_attempt_expiry(attempt.id)
    
    return tasks[0]


@router.post("/{token}/complete")
async def complete_assessment_endpoint(token: str):
    """
    Complete the assessment.
    
    This marks the assessment as completed and triggers metrics computation.
    """
    attempt = await get_attempt_by_token(token)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid assessment token",
        )
    
    try:
        result = await complete_assessment(attempt.id)
        return result
    except AttemptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    except AttemptLockedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assessment is not in progress",
        )


class EventRequest(BaseModel):
    """Request model for HTTP event fallback."""
    event_type: str
    task_id: str
    payload: Dict[str, Any] = {}
    client_timestamp: Optional[str] = None


@router.post("/{token}/event")
async def log_assessment_event(token: str, event_req: EventRequest, request: Request):
    """
    Log an assessment event via HTTP (fallback for WebSocket).
    
    This endpoint is used when WebSocket connection is unavailable.
    Only critical events (task_completed, task_started) use this fallback.
    """
    attempt = await get_attempt_by_token(token)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid assessment token",
        )
    
    if attempt.status.value not in ["pending", "in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assessment is not active",
        )
    
    try:
        event_type = EventType(event_req.event_type)
        event_data = EventCreate(
            task_id=event_req.task_id,
            event_type=event_type,
            payload=event_req.payload,
            client_timestamp=event_req.client_timestamp,
        )
        
        # Get client info from request
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        
        logged_event = await log_event(
            attempt_id=str(attempt.id),
            event_data=event_data,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        
        return {"status": "logged", "event_id": str(logged_event.id)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {event_req.event_type}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log event: {str(e)}",
        )
