"""
Skills API Endpoints
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.schemas import (
    SkillProfileResponse,
    CandidateListResponse,
    CandidateCompareRequest,
    CandidateCompareResponse,
    UserResponse,
)
from app.services import (
    generate_skill_profile,
    get_skill_profile,
    get_candidates_with_skills,
)
from app.dependencies import get_current_user
from app.core import AttemptNotFoundError


router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/attempt/{attempt_id}", response_model=SkillProfileResponse)
async def get_attempt_skill_profile(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get skill profile for a completed assessment.
    
    If not generated yet, returns 404. Use POST to generate.
    """
    skill = await get_skill_profile(attempt_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill profile not generated yet. Use POST to generate.",
        )
    return skill


@router.post("/attempt/{attempt_id}/generate", response_model=SkillProfileResponse)
async def generate_attempt_skill_profile(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Generate skill profile from computed metrics.
    
    This interprets the behavioral metrics into human-readable skill insights.
    All interpretations are deterministic and rule-based.
    """
    try:
        skill = await generate_skill_profile(attempt_id)
        return skill
    except AttemptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/candidates", response_model=CandidateListResponse)
async def list_candidates_with_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get list of candidates with skill summaries.
    
    Only includes candidates with completed assessments and generated skill profiles.
    """
    result = await get_candidates_with_skills(
        page=page, 
        page_size=page_size,
        user_id=current_user.id
    )
    return result


@router.post("/compare", response_model=CandidateCompareResponse)
async def compare_candidates(
    request: CandidateCompareRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Compare skill profiles for multiple candidates.
    """
    profiles = []
    for attempt_id in request.attempt_ids:
        profile = await get_skill_profile(attempt_id)
        if profile:
            profiles.append(profile)
    
    if not profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No skill profiles found for the given attempts",
        )
    
    return CandidateCompareResponse(candidates=profiles)
