"""
Kiwi Chatbot API Endpoint

Global chatbot endpoint that works across all dashboard pages.
Fetches real-time data based on page context (dashboard, candidates, skills, etc.)
"""

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import UserResponse
from app.dependencies import get_current_user
from app.services.ai_analyzer import (
    chat_with_candidate_context,
    chat_with_dashboard_context,
)


router = APIRouter(prefix="/kiwi", tags=["Kiwi Assistant"])


# ============================================================================
# REQUEST / RESPONSE MODELS
# ============================================================================

class KiwiChatMessage(BaseModel):
    role: str
    content: str

class KiwiChatRequest(BaseModel):
    query: str
    page_context: str = "general"  # dashboard | all_candidates | skill_reports | compare | live_assessment | settings | general
    attempt_id: Optional[str] = None
    history: Optional[List[KiwiChatMessage]] = None

class KiwiChatResponse(BaseModel):
    response: str
    context_used: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/chat", response_model=KiwiChatResponse)
async def kiwi_chat(
    request: KiwiChatRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Chat with Kiwi — the global dashboard assistant.
    
    Kiwi adapts its data context based on which page the recruiter is on:
    - dashboard: fetches stats (total candidates, active, completion rate)
    - all_candidates: fetches recent candidate list with statuses
    - skill_reports: fetches skill distribution data
    - live_assessment: fetches single candidate metrics (requires attempt_id)
    - settings / general: knowledge-base only, no dynamic data
    """
    # Convert history to dict format
    history = None
    if request.history:
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    # If attempt_id is provided, use the existing single-candidate context
    if request.attempt_id:
        from app.services.live_metrics_service import compute_live_metrics
        
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
        
        response = chat_with_candidate_context(
            query=request.query,
            context_data=context_data,
            conversation_history=history,
        )
        return KiwiChatResponse(response=response, context_used="live_assessment")
    
    # Otherwise, use dashboard-level context
    response = await chat_with_dashboard_context(
        query=request.query,
        page_context=request.page_context,
        recruiter_id=current_user.id,
        conversation_history=history,
    )
    
    return KiwiChatResponse(response=response, context_used=request.page_context)
