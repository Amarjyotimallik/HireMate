"""
Live Assessment API Endpoints

Real-time monitoring endpoints for recruiters to view active assessments.
"""

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import UserResponse
from app.dependencies import get_current_user
from app.services.live_metrics_service import (
    compute_live_metrics,
    get_active_assessments,
    get_completed_assessments,
)
from app.services.attempt_service import delete_attempt
from app.services.ai_analyzer import chat_with_candidate_context


router = APIRouter(prefix="/live-assessment", tags=["Live Assessment"])


# Request/Response models for chat
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    attempt_id: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str


@router.delete("/{attempt_id}", status_code=status.HTTP_200_OK)
async def delete_assessment(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Delete an assessment (ongoing or completed) and all its events.
    Only the recruiter who created the assessment can delete it.
    """
    try:
        result = await delete_attempt(attempt_id, recruiter_id=current_user.id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    return {
        "message": "Assessment deleted successfully",
        "attempt_id": attempt_id,
        "events_deleted": result.get("events_deleted", 0),
    }




@router.get("/active")
async def get_active_assessments_endpoint(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get all currently active (in-progress) assessments.
    
    Returns a list of assessments with basic info and progress.
    """
    assessments = await get_active_assessments(recruiter_id=current_user.id)
    return {"assessments": assessments, "total": len(assessments)}


@router.get("/completed")
async def get_completed_assessments_endpoint(
    limit: int = 10,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get recently completed assessments.
    """
    assessments = await get_completed_assessments(limit=limit, recruiter_id=current_user.id)
    return {"assessments": assessments, "total": len(assessments)}


@router.get("/{attempt_id}/stats")
async def get_live_stats(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get real-time statistics for a specific assessment.
    
    Returns current metrics computed from logged events.
    """
    stats = await compute_live_metrics(attempt_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    return stats


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Chat with the Report Assistant about the current candidate's data.
    """
    # Get live metrics for context
    context_data = await compute_live_metrics(request.attempt_id)
    
    if not context_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    
    # CRITICAL: Fetch the candidate's ACTUAL reasoning text from events
    # This ensures Kiwi shows real explanations instead of hallucinating
    from app.services.live_metrics_service import get_attempt_answers
    try:
        answers_data = await get_attempt_answers(request.attempt_id)
        context_data["live_answers"] = answers_data
    except Exception as e:
        context_data["live_answers"] = []
    
    # Convert history to dict format
    history = None
    if request.history:
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    # Generate response
    response = chat_with_candidate_context(
        query=request.query,
        context_data=context_data,
        conversation_history=history
    )
    
    return ChatResponse(response=response)

