"""
Email API Endpoints

Handles sending assessment invitation emails to candidates.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.services import get_attempt_by_id, send_assessment_email
from app.dependencies import get_current_user
from app.schemas import UserResponse
from app.config import get_settings


router = APIRouter(prefix="/email", tags=["Email"])


class SendAssessmentEmailRequest(BaseModel):
    """Request body for sending assessment email."""
    attempt_id: str
    to_email: Optional[EmailStr] = None  # Override candidate email if provided


class SendAssessmentEmailResponse(BaseModel):
    """Response for email sending."""
    success: bool
    message: str
    message_id: Optional[str] = None


@router.post("/send-assessment", response_model=SendAssessmentEmailResponse)
async def send_assessment_invitation(
    request: SendAssessmentEmailRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Send an assessment invitation email to the candidate.
    
    Uses the candidate's email from the attempt, or override with to_email.
    """
    settings = get_settings()
    
    if not settings.resend_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service not configured. Add RESEND_API_KEY to .env",
        )
    
    # Get attempt details
    attempt = await get_attempt_by_id(request.attempt_id)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    # Determine recipient email
    to_email = request.to_email or attempt.candidate_info.email
    if not to_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email address provided for candidate",
        )
    
    # Build assessment link
    # Use frontend URL from CORS origins (first one) or default
    frontend_url = settings.cors_origins_list[0] if settings.cors_origins_list else "http://localhost:5173"
    assessment_link = f"{frontend_url}/assessment/{attempt.token}"
    
    try:
        result = await send_assessment_email(
            to_email=to_email,
            candidate_name=attempt.candidate_info.name or "Candidate",
            assessment_link=assessment_link,
            position=attempt.candidate_info.position or "the position",
            expires_days=7,
        )
        
        return SendAssessmentEmailResponse(
            success=True,
            message=f"Assessment invitation sent to {to_email}",
            message_id=result.get("message_id"),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )
