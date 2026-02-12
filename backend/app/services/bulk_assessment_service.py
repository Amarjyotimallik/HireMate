"""
Bulk Assessment Service

Handles batch resume parsing, assessment creation, and progress tracking.
Supports two modes:
  - Celery + Redis (preferred): Parallel processing via distributed task queue
  - AsyncIO fallback: Sequential processing when Redis is unavailable
"""

import asyncio
import base64
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile

from app.config import get_settings
from app.db import get_database


# ── Redis / Celery Availability Check ──────────────────────────
_celery_available = False

def check_celery_available():
    """Check if Redis is reachable and Celery can dispatch tasks."""
    global _celery_available
    try:
        import redis
        redis_url = get_settings().redis_url
        r = redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        _celery_available = True
        print("[BULK] Redis connected - using Celery for parallel processing")
    except Exception as e:
        _celery_available = False
        print(f"[BULK] Redis unavailable ({e}) - falling back to async sequential processing")
    return _celery_available


# In-memory progress tracker for asyncio fallback
_active_jobs = {}


def get_active_jobs():
    """Get the active jobs tracker dict."""
    return _active_jobs


def is_celery_available():
    """Return whether Celery/Redis is available for parallel processing."""
    return _celery_available


async def create_bulk_job(recruiter_id: str, total_files: int, use_celery: bool = False) -> str:
    """
    Create a new bulk job record in the database.
    Returns the job_id.
    """
    db = get_database()
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()

    job_doc = {
        "job_id": job_id,
        "recruiter_id": recruiter_id,
        "status": "queued",
        "source_type": "local",
        "processing_mode": "celery" if use_celery else "async",
        "total_files": total_files,
        "processed_count": 0,
        "success_count": 0,
        "failed_count": 0,
        "current_file": None,
        "results": [],
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }


    await db.bulk_jobs.insert_one(job_doc)

    # Track in memory for fast access ONLY if using local asyncio processing
    # If using Celery, the worker updates the DB directly, so we shouldn't cache in memory
    # (otherwise the API server's stale memory cache will overwrite the DB values on read)
    if not use_celery:
        _active_jobs[job_id] = {
            "status": "queued",
            "total_files": total_files,
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "current_file": None,
        }

    return job_id


async def get_bulk_job(job_id: str, recruiter_id: str) -> Optional[dict]:
    """Get a bulk job by ID, scoped to the recruiter."""
    db = get_database()
    return await db.bulk_jobs.find_one({
        "job_id": job_id,
        "recruiter_id": recruiter_id,
    })


async def get_bulk_jobs_for_recruiter(recruiter_id: str, limit: int = 20) -> List[dict]:
    """Get all bulk jobs for a recruiter, newest first."""
    db = get_database()
    cursor = db.bulk_jobs.find(
        {"recruiter_id": recruiter_id}
    ).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ═══════════════════════════════════════════════════════════════
#  Celery-Based Processing (Parallel)
# ═══════════════════════════════════════════════════════════════

def dispatch_celery_tasks(job_id: str, files_data: List[dict], recruiter_id: str):
    """
    Dispatch individual Celery tasks for each resume file.
    Each file is processed in parallel by Celery workers.
    """
    from app.celery_tasks import process_single_resume

    for file_info in files_data:
        # Encode file content as base64 for JSON serialization
        file_payload = {
            'filename': file_info['filename'],
            'content_b64': base64.b64encode(file_info['content']).decode('utf-8'),
            'content_type': file_info['content_type'],
            'size': file_info['size'],
        }

        # Dispatch to Celery worker
        process_single_resume.apply_async(
            args=[job_id, file_payload, recruiter_id],
            queue='hiremate_bulk',
        )

    print(f"[BULK] Dispatched {len(files_data)} Celery tasks for job {job_id}")


async def check_celery_job_completion(job_id: str):
    """
    Check if all Celery tasks for this job have completed
    and update the job status accordingly.
    """
    db = get_database()
    job = await db.bulk_jobs.find_one({"job_id": job_id})
    if not job:
        return

    if job.get("processed_count", 0) >= job.get("total_files", 0):
        total = job.get("total_files", 0)
        failed = job.get("failed_count", 0)
        final_status = "completed" if failed < total else "failed"

        await db.bulk_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": final_status,
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "current_file": "",
            }}
        )

        # Clean up in-memory tracker
        if job_id in _active_jobs:
            del _active_jobs[job_id]


# ═══════════════════════════════════════════════════════════════
#  AsyncIO Fallback Processing (Sequential)
# ═══════════════════════════════════════════════════════════════

async def _update_job_progress(
    job_id: str,
    current_file: str,
    processed_count: int,
    success_count: int,
    failed_count: int,
    status: str = "processing",
):
    """Update job progress in both DB and memory."""
    db = get_database()
    now = datetime.utcnow()

    update_data = {
        "current_file": current_file,
        "processed_count": processed_count,
        "success_count": success_count,
        "failed_count": failed_count,
        "status": status,
        "updated_at": now,
    }
    if status in ("completed", "failed"):
        update_data["completed_at"] = now

    await db.bulk_jobs.update_one(
        {"job_id": job_id},
        {"$set": update_data},
    )

    # Update in-memory tracker
    if job_id in _active_jobs:
        _active_jobs[job_id].update(update_data)


async def _add_job_result(job_id: str, result: dict):
    """Append a result entry to the job's results array."""
    db = get_database()
    await db.bulk_jobs.update_one(
        {"job_id": job_id},
        {"$push": {"results": result}},
    )


async def process_bulk_resumes(
    job_id: str,
    files_data: List[dict],
    recruiter_id: str,
):
    """
    Process multiple resumes sequentially (asyncio fallback).
    Used when Redis/Celery is not available.
    """
    from app.utils.resume_parser import extract_text_from_file, parse_resume_text
    from app.services.attempt_service import create_attempt
    from app.schemas.attempt import AttemptCreate, CandidateInfo

    processed = 0
    successes = 0
    failures = 0

    # Mark job as processing
    await _update_job_progress(job_id, "", 0, 0, 0, "processing")

    for file_info in files_data:
        filename = file_info["filename"]
        content = file_info["content"]
        content_type = file_info["content_type"]
        file_size = file_info["size"]

        # Update current file being processed
        await _update_job_progress(
            job_id, filename, processed, successes, failures, "processing"
        )

        result = {
            "filename": filename,
            "file_size": file_size,
            "status": "processing",
            "assessment_id": None,
            "assessment_token": None,
            "candidate_name": None,
            "candidate_email": None,
            "position": None,
            "parsed_skills": [],
            "error_message": None,
            "email_sent": False,
            "email_sent_at": None,
            "processed_at": None,
        }

        try:
            # Step 1: Extract text from file
            text = extract_text_from_file(content, content_type, filename)
            if not text or len(text.strip()) < 10:
                raise ValueError("Could not extract meaningful text from file")

            # Step 2: Parse resume with AI
            parsed = parse_resume_text(text)
            candidate_name = parsed.get("name") or "Candidate"
            candidate_email = parsed.get("email") or f"candidate_{uuid.uuid4().hex[:8]}@pending.com"
            position = parsed.get("position") or "General Application"
            skills = parsed.get("skills") or []

            result["candidate_name"] = candidate_name
            result["candidate_email"] = candidate_email
            result["position"] = position
            result["parsed_skills"] = skills

            # Step 3: Create assessment attempt
            attempt_data = AttemptCreate(
                candidate_info=CandidateInfo(
                    name=candidate_name,
                    email=candidate_email,
                    position=position,
                    skills=skills,
                    resume_text=text,
                ),
                task_ids=[],
                expires_in_days=7,
            )

            attempt = await create_attempt(attempt_data, recruiter_id)

            result["status"] = "success"
            result["assessment_id"] = attempt.id
            result["assessment_token"] = attempt.token
            result["processed_at"] = datetime.utcnow()
            successes += 1

        except ValueError as e:
            result["status"] = "failed"
            result["error_message"] = str(e)
            result["processed_at"] = datetime.utcnow()
            failures += 1
            print(f"[BULK] Validation error for {filename}: {e}")

        except Exception as e:
            result["status"] = "failed"
            result["error_message"] = str(e)[:500]
            result["processed_at"] = datetime.utcnow()
            failures += 1
            print(f"[BULK] Error processing {filename}: {e}")

        processed += 1

        # Save result to DB
        await _add_job_result(job_id, result)

        # Update progress
        await _update_job_progress(
            job_id, filename, processed, successes, failures, "processing"
        )

        # Small delay between files to avoid overwhelming the AI API
        if processed < len(files_data):
            await asyncio.sleep(1)

    # Mark job as completed
    final_status = "completed" if failures < len(files_data) else "failed"
    await _update_job_progress(
        job_id, "", processed, successes, failures, final_status
    )

    # Clean up in-memory tracker
    if job_id in _active_jobs:
        del _active_jobs[job_id]

    print(f"[BULK] Job {job_id} completed: {successes} success, {failures} failed out of {processed} files")
