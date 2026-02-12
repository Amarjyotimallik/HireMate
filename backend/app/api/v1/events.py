"""
Events API Endpoints

Handles behavior event logging via REST API.
For real-time event logging, use WebSockets instead.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.schemas import (
    EventCreate,
    EventBatchCreate,
    EventResponse,
    EventListResponse,
    UserResponse,
)
from app.services import (
    log_event,
    log_events_batch,
    get_events_for_attempt,
    get_attempt_by_token,
    extend_attempt_expiry,
)
from app.dependencies import get_current_user, get_client_info
from app.core import (
    InvalidEventError,
    InvalidStateTransitionError,
    AttemptNotFoundError,
    AttemptLockedError,
)


router = APIRouter(prefix="/events", tags=["Behavior Events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def log_single_event(
    token: str,
    event_data: EventCreate,
    request: Request,
):
    """
    Log a single behavior event.
    
    The token is the assessment token (not JWT).
    Events are timestamped server-side and immediately stored in MongoDB.
    """
    # Get attempt from token
    attempt = await get_attempt_by_token(token)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid assessment token",
        )
    
    # Get client info
    client_info = await get_client_info(request)
    
    try:
        event = await log_event(
            attempt_id=attempt.id,
            event_data=event_data,
            user_agent=client_info.get("user_agent"),
            ip_address=client_info.get("ip_address"),
        )
        # Extend session expiry on activity
        await extend_attempt_expiry(attempt.id)
        return event
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
    except InvalidEventError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def log_batch_events(
    token: str,
    events_data: EventBatchCreate,
    request: Request,
):
    """
    Log multiple behavior events in a batch.
    
    Useful for catching up after brief disconnections.
    """
    # Get attempt from token
    attempt = await get_attempt_by_token(token)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid assessment token",
        )
    
    # Get client info
    client_info = await get_client_info(request)
    
    try:
        events = await log_events_batch(
            attempt_id=attempt.id,
            events_data=events_data,
            user_agent=client_info.get("user_agent"),
            ip_address=client_info.get("ip_address"),
        )
        # Extend session expiry on activity
        await extend_attempt_expiry(attempt.id)
        return {"logged": len(events), "events": events}
    except (AttemptNotFoundError, AttemptLockedError, InvalidEventError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/attempt/{attempt_id}", response_model=EventListResponse)
async def get_attempt_events(
    attempt_id: str,
    task_id: Optional[str] = None,
    event_type: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get all events for an attempt (recruiter view).
    
    Optionally filter by task_id or event_type.
    """
    try:
        events = await get_events_for_attempt(
            attempt_id=attempt_id,
            task_id=task_id,
            event_type=event_type,
        )
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
