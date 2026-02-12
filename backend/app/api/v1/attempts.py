"""
Attempts API Endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.schemas import (
    AttemptCreate,
    AttemptResponse,
    AttemptListResponse,
    UserResponse,
)
from app.schemas.resume import ATSScoreResponse
from app.services import (
    create_attempt,
    get_attempt_by_id,
    get_attempts,
    lock_attempt,
)
from app.services.ats_score_service import calculate_ats_score
from app.dependencies import get_current_user
from app.core import AttemptNotFoundError


router = APIRouter(prefix="/attempts", tags=["Attempts"])


@router.post("", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
async def create_new_attempt(
    attempt_data: AttemptCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Create a new assessment attempt for a candidate.
    
    This generates a one-time token that the candidate uses to access the assessment.
    The token expires after the specified number of days.
    """
    try:
        attempt = await create_attempt(attempt_data, current_user.id)
        return attempt
    except ValueError as e:
        # Duplicate email or validation error
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("", response_model=AttemptListResponse)
async def list_attempts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get paginated list of assessment attempts.
    """
    result = await get_attempts(
        page=page,
        page_size=page_size,
        status=status,
        user_id=current_user.id,
    )
    return result


@router.get("/{attempt_id}/ats-score", response_model=ATSScoreResponse)
async def get_attempt_ats_score(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get ATS score for this attempt's resume. 
    Calculates and caches the score if not already present.
    """
    from app.services.attempt_service import get_or_compute_ats_score
    
    result = await get_or_compute_ats_score(attempt_id)
    
    if not result:
        return ATSScoreResponse(
            ats_score=0.0,
            breakdown={"formatting": 0, "sections": 0, "contact": 0, "content": 0, "length": 0},
            formatting_issues=[],
            message="Attempt not found",
        )
        
    return ATSScoreResponse(**result)


@router.get("/{attempt_id}", response_model=AttemptResponse)
async def get_attempt(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get a specific attempt by ID.
    """
    attempt = await get_attempt_by_id(attempt_id)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found",
        )
    return attempt


@router.post("/{attempt_id}/lock", status_code=status.HTTP_200_OK)
async def lock_existing_attempt(
    attempt_id: str,
    reason: str = "manual_lock",
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Manually lock an attempt to prevent further activity.
    """
    success = await lock_attempt(attempt_id, reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found",
        )
    return {"message": "Attempt locked successfully", "attempt_id": attempt_id}
