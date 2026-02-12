"""
Metrics API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import (
    ComputedMetricsResponse,
    MetricsComputeRequest,
    UserResponse,
)
from app.services import compute_metrics, get_metrics
from app.dependencies import get_current_user
from app.core import AttemptNotFoundError, AttemptLockedError


router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/attempt/{attempt_id}", response_model=ComputedMetricsResponse)
async def get_attempt_metrics(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get computed metrics for a completed assessment.
    
    If metrics haven't been computed yet, returns 404.
    Use POST to trigger computation.
    """
    metrics = await get_metrics(attempt_id)
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metrics not computed yet. Use POST to compute.",
        )
    return metrics


@router.post("/attempt/{attempt_id}/compute", response_model=ComputedMetricsResponse)
async def compute_attempt_metrics(
    attempt_id: str,
    request: MetricsComputeRequest = MetricsComputeRequest(),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Compute or recompute metrics for a completed assessment.
    
    Metrics are computed from all logged behavior events.
    This happens AFTER the assessment is completed.
    """
    try:
        metrics = await compute_metrics(
            attempt_id=attempt_id,
            force_recompute=request.force_recompute,
        )
        return metrics
    except AttemptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    except AttemptLockedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment must be completed before computing metrics",
        )
