"""
ML Predictions API: interview success, job-fit, behavioral traits.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import UserResponse
from app.schemas.predictions import (
    InterviewSuccessRequest,
    InterviewSuccessResponse,
    JobFitPredictRequest,
    JobFitPredictResponse,
    BehavioralResponse,
)
from app.dependencies import get_current_user
from app.services.ml_predictions_service import (
    get_interview_success_prediction,
    get_behavioral_prediction,
    get_job_fit_prediction,
)


router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("/interview-success", response_model=InterviewSuccessResponse)
async def interview_success(
    body: InterviewSuccessRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Predict interview success probability for a completed attempt.
    Uses behavioral metrics; optionally includes resume/ATS in the score.
    """
    result = await get_interview_success_prediction(
        attempt_id=body.attempt_id,
        include_resume=body.include_resume,
    )
    return InterviewSuccessResponse(**result)


@router.post("/job-fit", response_model=JobFitPredictResponse)
async def job_fit(
    body: JobFitPredictRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Job fit score: resume vs job description (same engine as resume ATS score).
    """
    result = await get_job_fit_prediction(body.resume_text, body.job_description)
    return JobFitPredictResponse(**result)


@router.get("/behavioral/{attempt_id}", response_model=BehavioralResponse)
async def behavioral(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Predicted behavioral traits for an attempt (from computed metrics).
    """
    result = await get_behavioral_prediction(attempt_id)
    return BehavioralResponse(**result)
