"""
Resume / Document Upload API

Allows recruiters to upload a document (PDF or text), parse it for
name, email, phone, position, and optionally store the file for resume_url.
Also: ATS score, job-fit, and resume suggestions (ML plan).
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.config import get_settings
from app.schemas import UserResponse, ResumeParseResponse, CandidateInfoExtracted
from app.schemas.resume import (
    ATSScoreResponse,
    JobFitRequest,
    JobFitResponse,
    ResumeSuggestionsRequest,
    ResumeSuggestionsResponse,
    BatchAtsRequest,
    BatchAtsResponse,
    BatchAtsItemResponse,
    BatchSuggestionsRequest,
    BatchSuggestionsResponse,
)
from app.dependencies import get_current_user
from app.services import get_suggested_task_ids, get_attempt_by_id
from app.services.ats_score_service import calculate_ats_score
from app.services.resume_suggestions_service import get_suggestions
from app.utils.resume_parser import extract_text_from_file, parse_resume_text


router = APIRouter(prefix="/resume", tags=["Resume"])

ALLOWED_CONTENT_TYPES = {"application/pdf", "text/plain"}
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


def _ensure_upload_dir() -> Path:
    """Ensure upload directory exists and return its path."""
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.is_absolute():
        # Relative to backend root (parent of app)
        upload_dir = Path(__file__).resolve().parent.parent.parent / settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _save_upload(content: bytes, filename: str) -> str:
    """Save file to upload dir with unique id. Returns file_id (uuid)."""
    upload_path = _ensure_upload_dir()
    ext = Path(filename).suffix.lower() if filename else ".bin"
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".pdf"
    file_id = str(uuid.uuid4())
    dest = upload_path / f"{file_id}{ext}"
    dest.write_bytes(content)
    return file_id


@router.post("/parse", response_model=ResumeParseResponse, status_code=status.HTTP_200_OK)
async def upload_and_parse_resume(
    file: UploadFile = File(..., description="PDF or plain text resume document"),
):
    """
    Upload a resume document (PDF or .txt), parse it for candidate info.

    Extracts name, email, phone, position for use when creating an assessment attempt.
    Optionally stores the file and returns resume_url for candidate_info.resume_url.
    """
    settings = get_settings()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.max_upload_size_mb} MB",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    content_type = file.content_type or ""
    filename = file.filename or ""

    if content_type not in ALLOWED_CONTENT_TYPES and not any(
        filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Use PDF or plain text (.txt).",
        )

    try:
        text = extract_text_from_file(content, content_type, filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    parsed = parse_resume_text(text)

    # Optional: store file and return resume_url
    file_id = _save_upload(content, filename)
    resume_url = f"/api/v1/resume/files/{file_id}"

    # Suggest task IDs from parsed position so questions relate to the resume
    suggested_task_ids = await get_suggested_task_ids(parsed.get("position"), limit=2)

    return ResumeParseResponse(
        candidate_info=CandidateInfoExtracted(
            name=parsed.get("name"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            position=parsed.get("position"),
            skills=parsed.get("skills") or [],
            resume_text=text,
        ),
        resume_url=resume_url,
        resume_text=text,
        suggested_task_ids=suggested_task_ids or None,
    )


@router.get("/files/{file_id}")
async def get_resume_file(
    file_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Download a previously uploaded resume file by id.
    """
    upload_path = _ensure_upload_dir()
    safe_id = file_id.strip().replace("..", "")
    for ext in ALLOWED_EXTENSIONS:
        path = upload_path / f"{safe_id}{ext}"
        if path.is_file():
            from fastapi.responses import FileResponse
            return FileResponse(
                path,
                filename=f"resume{ext}",
                media_type="application/pdf" if ext == ".pdf" else "text/plain",
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


# ----- ML: ATS score, job-fit, resume suggestions -----


@router.get("/ats-by-attempt/{attempt_id}", response_model=ATSScoreResponse)
async def ats_score_by_attempt(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get ATS score for an attempt's resume (by attempt ID). Always returns 200;
    use message when attempt not found or no resume text.
    """
    attempt = await get_attempt_by_id(attempt_id)
    if not attempt:
        return ATSScoreResponse(
            ats_score=0.0,
            breakdown={"formatting": 0, "sections": 0, "contact": 0, "content": 0, "length": 0},
            formatting_issues=[],
            message="Attempt not found",
        )
    resume_text = (attempt.candidate_info and getattr(attempt.candidate_info, "resume_text", None)) or ""
    if not (resume_text and resume_text.strip()):
        return ATSScoreResponse(
            ats_score=0.0,
            breakdown={"formatting": 0, "sections": 0, "contact": 0, "content": 0, "length": 0},
            formatting_issues=[],
            message="No resume text for this attempt",
        )
    result = calculate_ats_score(resume_text, "")
    return ATSScoreResponse(**result)


@router.post("/ats-score", response_model=ATSScoreResponse)
async def ats_score(
    body: JobFitRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Calculate ATS score for resume vs job description (embedding + keywords + formatting).
    """
    result = calculate_ats_score(body.resume_text, body.job_description)
    return ATSScoreResponse(**result)


@router.post("/job-fit", response_model=JobFitResponse)
async def job_fit(
    body: JobFitRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Job fit score (resume vs JD) with breakdown. Same engine as ATS score.
    """
    result = calculate_ats_score(body.resume_text, body.job_description)
    return JobFitResponse(
        fit_score=result["ats_score"],
        breakdown=result["breakdown"],
        suggestions=[f["fix"] for f in result.get("formatting_issues", [])[:5]],
    )


@router.post("/suggestions", response_model=ResumeSuggestionsResponse)
async def resume_suggestions(
    body: ResumeSuggestionsRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get resume suggestions: missing keywords, formatting, skills gap, content quality.
    Optionally pass job_description and suggestion_types (keywords, formatting, skills, content).
    """
    data = get_suggestions(
        resume_text=body.resume_text,
        job_description=body.job_description,
        suggestion_types=body.suggestion_types,
    )
    return ResumeSuggestionsResponse(**data)


# ----- Phase 6: Batch operations -----


@router.post("/batch-ats-score", response_model=BatchAtsResponse)
async def batch_ats_score(
    body: BatchAtsRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Score multiple resumes against one job description. Returns ATS score per resume.
    """
    results = []
    for i, resume_text in enumerate(body.resume_texts):
        result = calculate_ats_score(resume_text, body.job_description)
        results.append(BatchAtsItemResponse(
            index=i,
            ats_score=result["ats_score"],
            breakdown=result.get("breakdown", {}),
        ))
    return BatchAtsResponse(results=results)


@router.post("/batch-suggestions", response_model=BatchSuggestionsResponse)
async def batch_suggestions(
    body: BatchSuggestionsRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get resume suggestions for multiple resume+JD pairs. Returns one suggestions object per item.
    """
    results = []
    for item in body.items:
        data = get_suggestions(
            resume_text=item.resume_text,
            job_description=item.job_description,
            suggestion_types=None,
        )
        results.append(ResumeSuggestionsResponse(**data))
    return BatchSuggestionsResponse(results=results)
