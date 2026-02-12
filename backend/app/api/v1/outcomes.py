"""
Outcomes API

Endpoints for logging hiring decisions and getting calibration data.
This enables future correlation between HireMate predictions and actual outcomes.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_current_user
from app.services.population_stats_service import (
    log_hiring_decision,
    get_calibration_stats,
)


router = APIRouter(prefix="/outcomes", tags=["outcomes"])


# ============================================================================
# SCHEMAS
# ============================================================================

class DecisionLogRequest(BaseModel):
    """Request to log a hiring decision."""
    decision: str  # "hire", "no_hire", "pending"
    notes: Optional[str] = None
    metrics_snapshot: Optional[dict] = None


class DecisionLogResponse(BaseModel):
    """Response after logging a decision."""
    status: str
    attempt_id: str


class CalibrationStatsResponse(BaseModel):
    """Calibration statistics for a recruiter."""
    total_decisions: int
    hired: int
    rejected: int
    pending: int
    calibration_ready: bool
    message: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/{attempt_id}", response_model=DecisionLogResponse)
async def log_decision(
    attempt_id: str,
    request: DecisionLogRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Log a hiring decision for a candidate.
    
    This data is used for future calibration studies to correlate
    HireMate predictions with actual hiring outcomes.
    
    Valid decisions: "hire", "no_hire", "pending"
    """
    valid_decisions = ["hire", "no_hire", "pending"]
    if request.decision not in valid_decisions:
        raise HTTPException(
            status_code=400, 
            detail=f"Decision must be one of: {valid_decisions}"
        )
    
    result = await log_hiring_decision(
        attempt_id=attempt_id,
        decision=request.decision,
        recruiter_id=str(current_user["_id"]),
        metrics_snapshot=request.metrics_snapshot,
        notes=request.notes
    )
    
    return DecisionLogResponse(**result)


@router.get("/calibration", response_model=CalibrationStatsResponse)
async def get_calibration(
    current_user: dict = Depends(get_current_user)
):
    """
    Get calibration statistics for the current recruiter.
    
    Shows how many decisions have been logged and whether
    there's enough data for meaningful calibration analysis.
    """
    stats = await get_calibration_stats(
        recruiter_id=str(current_user["_id"])
    )
    
    return CalibrationStatsResponse(**stats)
