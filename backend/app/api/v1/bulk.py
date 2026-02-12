"""
Bulk Assessment API Endpoints

Handles multi-file resume upload, batch assessment creation,
progress tracking, and bulk email sending.
"""

import asyncio
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from bson import ObjectId

from app.config import get_settings
from app.dependencies import get_current_user
from app.schemas import UserResponse
from app.schemas.bulk import (
    BulkJobResponse,
    BulkJobStatusResponse,
    BulkFileResult,
    BulkEmailRequest,
    BulkEmailResponse,
    BulkEmailResultItem,
    BulkJobListResponse,
    BulkResultStatus,
)
from app.services.bulk_assessment_service import (
    create_bulk_job,
    get_bulk_job,
    get_bulk_jobs_for_recruiter,
    process_bulk_resumes,
    get_active_jobs,
)
from app.services.email_service import send_assessment_email
from app.db import get_database


router = APIRouter(prefix="/bulk", tags=["Bulk Assessment"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_BULK_FILES = 100


@router.post("/create", response_model=BulkJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_bulk_assessments(
    files: List[UploadFile] = File(..., description="Multiple resume files (PDF, TXT, DOCX)"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Upload multiple resumes and create assessments for each candidate.

    Accepts up to 100 files. Processing happens in the background.
    Returns a job_id to track progress via /bulk/status/{job_id}.
    """
    settings = get_settings()

    # Validate file count
    if len(files) > MAX_BULK_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files. Maximum {MAX_BULK_FILES} files per batch.",
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided.",
        )

    # Read and validate all files upfront
    files_data = []
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    for f in files:
        filename = f.filename or "unknown"
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            # Skip unsupported files silently — they'll appear as "skipped" in results
            continue

        content = await f.read()
        if len(content) == 0:
            continue
        if len(content) > max_bytes:
            continue

        files_data.append({
            "filename": filename,
            "content": content,
            "content_type": f.content_type or "application/octet-stream",
            "size": len(content),
        })

    if not files_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid files found. Supported formats: PDF, TXT, DOCX.",
        )

    # Check if Celery/Redis is available for parallel processing
    from app.services.bulk_assessment_service import is_celery_available, dispatch_celery_tasks
    use_celery = is_celery_available()

    # Create job record
    job_id = await create_bulk_job(current_user.id, len(files_data), use_celery=use_celery)

    if use_celery:
        # Use Celery for parallel processing
        dispatch_celery_tasks(job_id, files_data, current_user.id)
        mode_msg = "(parallel processing via Celery)"
    else:
        # Fall back to AsyncIO sequential processing
        asyncio.create_task(
            process_bulk_resumes(job_id, files_data, current_user.id)
        )
        mode_msg = "(sequential processing - Redis unavailable)"

    return BulkJobResponse(
        job_id=job_id,
        total_files=len(files_data),
        message=f"Processing {len(files_data)} resumes in background {mode_msg}. Poll /bulk/status/{job_id} for progress.",
    )


@router.get("/status/{job_id}", response_model=BulkJobStatusResponse)
async def get_bulk_job_status(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get the current status of a bulk processing job.

    Returns progress counts and per-file results.
    """
    job = await get_bulk_job(job_id, current_user.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bulk job not found.",
        )

    # Merge live progress from in-memory tracker if still active
    active_jobs = get_active_jobs()
    if job_id in active_jobs:
        live = active_jobs[job_id]
        job["processed_count"] = live.get("processed_count", job.get("processed_count", 0))
        job["success_count"] = live.get("success_count", job.get("success_count", 0))
        job["failed_count"] = live.get("failed_count", job.get("failed_count", 0))
        job["current_file"] = live.get("current_file", job.get("current_file"))
        job["status"] = live.get("status", job.get("status"))

    return BulkJobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        total_files=job.get("total_files", 0),
        processed_count=job.get("processed_count", 0),
        success_count=job.get("success_count", 0),
        failed_count=job.get("failed_count", 0),
        current_file=job.get("current_file"),
        results=[BulkFileResult(**r) for r in job.get("results", [])],
        created_at=job.get("created_at"),
        updated_at=job.get("updated_at"),
        completed_at=job.get("completed_at"),
    )


@router.get("/jobs", response_model=BulkJobListResponse)
async def list_bulk_jobs(
    limit: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    List all bulk jobs for the current recruiter, newest first.
    """
    jobs = await get_bulk_jobs_for_recruiter(current_user.id, limit)

    job_responses = []
    for job in jobs:
        job_responses.append(BulkJobStatusResponse(
            job_id=job["job_id"],
            status=job["status"],
            total_files=job.get("total_files", 0),
            processed_count=job.get("processed_count", 0),
            success_count=job.get("success_count", 0),
            failed_count=job.get("failed_count", 0),
            current_file=job.get("current_file"),
            results=[BulkFileResult(**r) for r in job.get("results", [])],
            created_at=job.get("created_at"),
            updated_at=job.get("updated_at"),
            completed_at=job.get("completed_at"),
        ))

    return BulkJobListResponse(
        jobs=job_responses,
        total=len(job_responses),
    )


@router.post("/email", response_model=BulkEmailResponse)
async def send_bulk_emails(
    request: BulkEmailRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Send assessment emails to multiple candidates at once.

    Accepts a list of assessment IDs and sends the assessment link
    to each candidate's email.
    """
    db = get_database()
    settings = get_settings()
    frontend_url = settings.cors_origins_list[0] if settings.cors_origins_list else "http://localhost:5173"

    results = []
    success_count = 0
    failed_count = 0

    for assessment_id in request.assessment_ids:
        try:
            # Find the attempt
            attempt = await db.task_attempts.find_one({
                "_id": ObjectId(assessment_id),
                "created_by": current_user.id,
            })

            if not attempt:
                results.append(BulkEmailResultItem(
                    assessment_id=assessment_id,
                    status="failed",
                    error="Assessment not found",
                ))
                failed_count += 1
                continue

            candidate_info = attempt.get("candidate_info", {})
            candidate_email = candidate_info.get("email")
            candidate_name = candidate_info.get("name", "Candidate")
            position = candidate_info.get("position", "the position")
            token = attempt.get("token")

            if not candidate_email:
                results.append(BulkEmailResultItem(
                    assessment_id=assessment_id,
                    status="failed",
                    error="No email address for this candidate",
                ))
                failed_count += 1
                continue

            # Build assessment link
            assessment_link = f"{frontend_url}/assessment/{token}"

            # Send email
            await send_assessment_email(
                to_email=candidate_email,
                candidate_name=candidate_name,
                assessment_link=assessment_link,
                position=position,
            )

            # Update the attempt document to mark email as sent
            from datetime import datetime
            await db.task_attempts.update_one(
                {"_id": ObjectId(assessment_id)},
                {"$set": {
                    "email_sent": True,
                    "email_sent_at": datetime.utcnow(),
                }},
            )

            results.append(BulkEmailResultItem(
                assessment_id=assessment_id,
                status="success",
            ))
            success_count += 1

        except Exception as e:
            results.append(BulkEmailResultItem(
                assessment_id=assessment_id,
                status="failed",
                error=str(e)[:200],
            ))
            failed_count += 1

        # Small delay between emails to avoid rate limits
        await asyncio.sleep(0.5)

    return BulkEmailResponse(
        total=len(request.assessment_ids),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
    )


@router.post("/retry/{job_id}")
async def retry_failed_files(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Retry processing for any failed files in a bulk job.
    
    Note: This creates a new job with only the failed files.
    Original file content is not stored, so the user must re-upload.
    """
    job = await get_bulk_job(job_id, current_user.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bulk job not found.",
        )

    failed_files = [r for r in job.get("results", []) if r.get("status") == "failed"]

    if not failed_files:
        return {"message": "No failed files to retry.", "failed_count": 0}

    return {
        "message": f"Found {len(failed_files)} failed files. Please re-upload them using /bulk/create.",
        "failed_count": len(failed_files),
        "failed_files": [f["filename"] for f in failed_files],
    }
