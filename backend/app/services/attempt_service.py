"""
Attempt Service

Handles assessment attempt creation and management.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from bson import ObjectId

from app.config import get_settings
from app.core import (
    generate_assessment_token,
    AttemptNotFoundError,
    AttemptLockedError,
    AttemptExpiredError,
    TokenAlreadyUsedError,
    InvalidTokenError,
)
from app.db import get_attempts_collection
from app.schemas import (
    AttemptCreate,
    AttemptResponse,
    AttemptBrief,
    AttemptListResponse,
    AttemptStatus,
    AssessmentInfo,
    CandidateInfo,
)
from app.services.ats_score_service import calculate_ats_score


# Token expiry settings (activity-based)
IDLE_TIMEOUT_MINUTES = 30  # Token expires after 30 min of inactivity
MAX_SESSION_HOURS = 24     # Hard limit: 24 hours max session duration


async def extend_attempt_expiry(attempt_id: str) -> bool:
    """
    Extend the attempt expiry based on activity.
    Called on each candidate interaction to keep the session alive.
    
    Returns True if expiry was extended, False if attempt not found or already completed.
    """
    attempts = get_attempts_collection()
    now = datetime.utcnow()
    new_expiry = now + timedelta(minutes=IDLE_TIMEOUT_MINUTES)
    
    result = await attempts.update_one(
        {
            "_id": ObjectId(attempt_id),
            "status": {"$in": [AttemptStatus.PENDING.value, AttemptStatus.IN_PROGRESS.value]}
        },
        {
            "$set": {
                "last_activity_at": now,
                "expires_at": new_expiry,
                "updated_at": now
            }
        }
    )
    
    return result.modified_count > 0


async def create_attempt(attempt_data: AttemptCreate, user_id: str) -> AttemptResponse:
    """Create a new assessment attempt with one-time token."""
    attempts = get_attempts_collection()
    settings = get_settings()
    
    # Check for existing active assessment with same email
    candidate_email = attempt_data.candidate_info.email
    if candidate_email:
        existing = await attempts.find_one({
            "candidate_info.email": candidate_email,
            "status": {"$in": [AttemptStatus.PENDING.value, AttemptStatus.IN_PROGRESS.value]},
            "created_by": user_id,  # Only check within same recruiter's assessments
        })
        if existing:
            raise ValueError(
                f"An active assessment already exists for {candidate_email}. "
                "Please wait for it to complete or cancel it before creating a new one."
            )
    
    now = datetime.utcnow()
    expires_at = now + timedelta(days=attempt_data.expires_in_days)
    
    # Generate unique token
    token = generate_assessment_token()

    # Dynamic Question Generation
    task_ids = attempt_data.task_ids
    if not task_ids:
        try:
            from app.services.question_service import generate_questions_from_resume
            from app.services.task_service import create_task
            
            # Use resume text and skills for generation
            # Fallback to position-based if no resume text? 
            # For now, rely on what's passed.
            print(f"[INFO] Generating questions for resume length: {len(attempt_data.candidate_info.resume_text or '')}")
            generated_tasks = await generate_questions_from_resume(
                attempt_data.candidate_info.resume_text or f"Position: {attempt_data.candidate_info.position}",
                attempt_data.candidate_info.skills or [],
                num_questions=10  # Increased to 10 per request
            )
            print(f"[INFO] Received {len(generated_tasks)} generated tasks")
            
            generated_ids = []
            for task_data in generated_tasks:
                new_task = await create_task(task_data, user_id)
                generated_ids.append(new_task.id)
            
            print(f"[INFO] Created {len(generated_ids)} tasks in DB: {generated_ids}")
            
            if generated_ids:
                task_ids = generated_ids
        except Exception as e:
            print(f"[ERROR] Failed to generate dynamic tasks: {e}")
            # Fallback: get some default tasks?
            # Ideally we should fail or used suggested tasks.
            # Let's try to get suggested tasks as fallback
            try:
                from app.services.task_service import get_suggested_task_ids
                task_ids = await get_suggested_task_ids(attempt_data.candidate_info.position, limit=10)
            except:
                pass

    if not task_ids:
        # Final safety check: Do not create empty assessments
        print("[ERROR] Attempt creation failed: No tasks could be generated or assigned.")
        raise ValueError("Failed to generate assessment questions. Please try again.")

    attempt_doc = {
        "token": token,
        "candidate_info": attempt_data.candidate_info.model_dump(),
        "task_ids": task_ids,
        "created_by": user_id,
        "status": AttemptStatus.PENDING.value,
        "started_at": None,
        "completed_at": None,
        "expires_at": expires_at,
        "current_task_index": 0,
        "locked_at": None,
        "locked_reason": None,
        "created_at": now,
        "updated_at": now,
    }
    
    result = await attempts.insert_one(attempt_doc)
    
    print(f"[INFO] Attempt created with ID: {result.inserted_id}, Token: {token}, Task IDs: {task_ids}")
    
    return AttemptResponse(
        id=str(result.inserted_id),
        token=token,
        candidate_info=attempt_data.candidate_info,
        task_ids=task_ids,
        status=AttemptStatus.PENDING,
        created_by=user_id,
        started_at=None,
        completed_at=None,
        expires_at=expires_at,
        current_task_index=0,
        created_at=now,
        analysis_result=None
    )


async def get_attempt_by_id(attempt_id: str) -> Optional[AttemptResponse]:
    """Get attempt by ID."""
    attempts = get_attempts_collection()
    
    try:
        attempt = await attempts.find_one({"_id": ObjectId(attempt_id)})
    except Exception:
        return None
    
    if not attempt:
        return None
    
    return _attempt_doc_to_response(attempt)


def _attempt_doc_to_response(attempt: dict) -> AttemptResponse:
    return AttemptResponse(
        id=str(attempt["_id"]),
        token=attempt["token"],
        candidate_info=CandidateInfo(**attempt["candidate_info"]),
        task_ids=attempt["task_ids"],
        status=AttemptStatus(attempt["status"]),
        created_by=attempt["created_by"],
        started_at=attempt.get("started_at"),
        completed_at=attempt.get("completed_at"),
        expires_at=attempt["expires_at"],
        current_task_index=attempt["current_task_index"],
        created_at=attempt.get("created_at"),
        analysis_result=attempt.get("analysis_result")
    )


async def get_attempt_by_token(token: str) -> Optional[AttemptResponse]:
    """Get attempt by token."""
    attempts = get_attempts_collection()
    
    attempt = await attempts.find_one({"token": token})
    if not attempt:
        return None
    
    return _attempt_doc_to_response(attempt)


async def validate_and_get_assessment(token: str) -> AssessmentInfo:
    """Validate token and return assessment info for candidates."""
    attempts = get_attempts_collection()
    
    print(f"[DEBUG] Validating assessment token: {token}")
    attempt = await attempts.find_one({"token": token})
    
    if not attempt:
        print(f"[ERROR] Token not found: {token}")
        raise InvalidTokenError("Invalid assessment token")
    
    print(f"[DEBUG] Found attempt: {attempt.get('_id')}, Tasks: {len(attempt.get('task_ids', []))}")
    
    # Check expiration
    if attempt["expires_at"] < datetime.utcnow():
        raise AttemptExpiredError("Assessment has expired")
    
    # Check status
    status = attempt["status"]
    if status in [AttemptStatus.COMPLETED.value, AttemptStatus.LOCKED.value]:
        raise AttemptLockedError("Assessment has already been completed")
    
    if status == AttemptStatus.EXPIRED.value:
        raise AttemptExpiredError("Assessment has expired")
    
    return AssessmentInfo(
        attempt_id=str(attempt["_id"]),
        candidate_name=attempt["candidate_info"]["name"],
        position=attempt["candidate_info"]["position"],
        total_tasks=len(attempt["task_ids"]),
        current_task_index=attempt["current_task_index"],
        status=AttemptStatus(status),
        expires_at=attempt["expires_at"],
    )


async def start_assessment(token: str) -> dict:
    """Start an assessment (consumes the token)."""
    attempts = get_attempts_collection()
    
    attempt = await attempts.find_one({"token": token})
    
    if not attempt:
        raise InvalidTokenError("Invalid assessment token")
    
    # Check if already started
    if attempt["status"] != AttemptStatus.PENDING.value:
        if attempt["status"] == AttemptStatus.IN_PROGRESS.value:
            # Already in progress, allow continuing
            return {
                "attempt_id": str(attempt["_id"]),
                "message": "Assessment resumed",
                "total_tasks": len(attempt["task_ids"]),
                "current_task_index": attempt["current_task_index"],
            }
        raise TokenAlreadyUsedError("Assessment token has already been used")
    
    # Check expiration
    if attempt["expires_at"] < datetime.utcnow():
        raise AttemptExpiredError("Assessment has expired")
    
    # Update status to in_progress
    now = datetime.utcnow()
    await attempts.update_one(
        {"_id": attempt["_id"]},
        {
            "$set": {
                "status": AttemptStatus.IN_PROGRESS.value,
                "started_at": now,
                "updated_at": now,
            }
        }
    )
    
    return {
        "attempt_id": str(attempt["_id"]),
        "message": "Assessment started",
        "total_tasks": len(attempt["task_ids"]),
        "current_task_index": 0,
    }


async def complete_assessment(attempt_id: str) -> dict:
    """Mark an assessment as completed."""
    attempts = get_attempts_collection()
    
    attempt = await attempts.find_one({"_id": ObjectId(attempt_id)})
    
    if not attempt:
        raise AttemptNotFoundError("Assessment not found")
    
    if attempt["status"] != AttemptStatus.IN_PROGRESS.value:
        raise AttemptLockedError("Assessment is not in progress")
    
    now = datetime.utcnow()
    update_result = await attempts.update_one(
        {"_id": ObjectId(attempt_id)},
        {
            "$set": {
                "status": AttemptStatus.COMPLETED.value,
                "completed_at": now,
                "updated_at": now,
            }
        }
    )

    try:
        from app.api.websocket.manager import manager
        await manager.broadcast_to_monitors(attempt_id, {
            "type": "status_update",
            "attempt_id": attempt_id,
            "status": AttemptStatus.COMPLETED.value,
            "current_task_index": attempt.get("current_task_index", 0),
            "total_tasks": len(attempt.get("task_ids", [])),
            "completed_at": now.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        })
        await manager.broadcast_to_monitors(attempt_id, {
            "type": "assessment_completed",
            "attempt_id": attempt_id,
            "completed_at": now.isoformat(),
        })
    except Exception as ws_e:
        print(f"[WARNING] Failed to broadcast completion status: {ws_e}")
    
    # CRITICAL FIX: Explicitly compute and PERSIST metrics to DB for ML predictions
    try:
        from app.services.metrics_service import compute_metrics
        await compute_metrics(attempt_id, force_recompute=True)
        print(f"[INFO] Metrics computed and persisted for attempt {attempt_id}")
    except Exception as e:
        print(f"[ERROR] Failed to persist metrics: {e}")

    
    # Debug: Verify the update happened
    print(f"[DEBUG] complete_assessment: attempt_id={attempt_id}")
    print(f"[DEBUG] complete_assessment: update_result.matched_count={update_result.matched_count}, modified_count={update_result.modified_count}")
    
    # Generate Final AI Report (Batch)
    try:
        from app.services.live_metrics_service import compute_live_metrics, get_attempt_answers
        from app.services.ai_analyzer import analyze_full_assessment_batch
        
        # Calculate metrics for the completed attempt (for speed/focus/etc)
        metrics = await compute_live_metrics(attempt_id)
        
        # Fetch all detailed answers
        answers_data = await get_attempt_answers(attempt_id)
        
        # Extract necessary data
        candidate_info = attempt.get("candidate_info", {})
        candidate_name = candidate_info.get("name", "Candidate")
        position = candidate_info.get("position", "Role")
        
        # Generate BATCH report (Single API Call)
        final_report = None
        
        if answers_data:
            report_data = analyze_full_assessment_batch(
                candidate_name=candidate_name,
                position=position,
                answers=answers_data,
                metrics=metrics  # Pass behavioral metrics
            )
            
            # Helper to merge the batch verdict with the existing metrics structure
            # effectively overriding the verdict with the AI one.
            final_report = {
                "verdict": report_data.get("final_verdict", {}).get("verdict"),
                "recommendation": report_data.get("final_verdict", {}).get("recommendation"),
                "strengths": report_data.get("final_verdict", {}).get("strengths"),
                "improvements": report_data.get("final_verdict", {}).get("improvements"),
                "per_question_analysis": report_data.get("per_question_analysis", []),
                "generated_at": datetime.utcnow().isoformat()
            }
        else:
            print(f"[WARNING] No answers found for attempt {attempt_id}. Using fallback report.")
            final_report = {
                "verdict": "Inconclusive (No Data)",
                "recommendation": "The assessment was completed but no response data was captured to analyze.",
                "strengths": ["N/A"],
                "improvements": ["Data Capture Failed"],
                "per_question_analysis": [],
                "generated_at": datetime.utcnow().isoformat()
            }

        if final_report:
            # Save report and cache overall_fit for quick list access
            await attempts.update_one(
                {"_id": ObjectId(attempt_id)},
                {
                    "$set": {
                        "analysis_result": final_report,
                        "cached_overall_fit": metrics.get("overall_fit", {})
                    }
                }
            )

            # BROADCAST: Notify frontend that analysis is ready!
            try:
                from app.api.websocket.manager import manager
                # Re-compute to include the newly saved verdict
                updated_metrics = await compute_live_metrics(attempt_id)
                
                await manager.broadcast_to_monitors(attempt_id, {
                    "type": "metrics_update",
                    "attempt_id": attempt_id,
                    "metrics": updated_metrics,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception as ws_e:
                print(f"[WARNING] Failed to broadcast final report: {ws_e}")
        
    except Exception as e:
        import traceback
        error_msg = f"[ERROR] Final report generation failed: {e}\n{traceback.format_exc()}"
        print(error_msg)
        try:
            with open("backend_error.log", "a") as f:
                f.write(f"{datetime.utcnow().isoformat()} - {error_msg}\n")
        except:
            pass
    
    return {
        "attempt_id": attempt_id,
        "message": "Assessment completed",
        "completed_at": now.isoformat(),
    }


async def update_task_progress(attempt_id: str, task_index: int) -> bool:
    """Update current task index."""
    attempts = get_attempts_collection()
    
    result = await attempts.update_one(
        {"_id": ObjectId(attempt_id)},
        {
            "$set": {
                "current_task_index": task_index,
                "updated_at": datetime.utcnow(),
            }
        }
    )
    
    return result.modified_count > 0


async def lock_attempt(attempt_id: str, reason: str = "manual_lock") -> bool:
    """Manually lock an attempt."""
    attempts = get_attempts_collection()
    
    now = datetime.utcnow()
    result = await attempts.update_one(
        {"_id": ObjectId(attempt_id)},
        {
            "$set": {
                "status": AttemptStatus.LOCKED.value,
                "locked_at": now,
                "locked_reason": reason,
                "updated_at": now,
            }
        }
    )
    
    return result.modified_count > 0


async def delete_attempt(attempt_id: str, recruiter_id: str) -> dict:
    """
    Delete an assessment attempt and all its associated events.
    Only the recruiter who created the attempt can delete it.
    """
    from app.db import get_events_collection
    
    attempts = get_attempts_collection()
    
    # Find the attempt and verify ownership
    try:
        attempt = await attempts.find_one({"_id": ObjectId(attempt_id)})
    except Exception:
        return None
    
    if not attempt:
        return None
    
    # Ownership check
    if attempt.get("created_by") != recruiter_id:
        raise PermissionError("You can only delete your own assessments")
    
    # Delete all events for this attempt
    events_coll = get_events_collection()
    events_result = await events_coll.delete_many({
        "$or": [
            {"attempt_id": attempt_id},
            {"attempt_id": ObjectId(attempt_id)},
        ]
    })
    
    # Delete the attempt document
    attempt_result = await attempts.delete_one({"_id": ObjectId(attempt_id)})
    
    return {
        "deleted": attempt_result.deleted_count > 0,
        "events_deleted": events_result.deleted_count,
    }


async def get_attempts(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    user_id: Optional[str] = None,
) -> AttemptListResponse:
    """Get paginated list of attempts."""
    attempts = get_attempts_collection()
    
    # Build query
    query = {}
    if status:
        query["status"] = status
    if user_id:
        query["created_by"] = user_id
    
    # Get total count
    total = await attempts.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * page_size
    cursor = attempts.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    
    attempt_list = []
    async for attempt in cursor:
        # Extract score safely
        analysis = attempt.get("analysis_result", {}) or {}
        overall_fit = analysis.get("overall_fit", {}) or {}
        # Fallback to cached if available (optimization from complete_assessment)
        if not overall_fit and "cached_overall_fit" in attempt:
             overall_fit = attempt["cached_overall_fit"] or {}

        attempt_list.append(AttemptBrief(
            id=str(attempt["_id"]),
            candidate_name=attempt["candidate_info"]["name"],
            candidate_email=attempt["candidate_info"]["email"],
            position=attempt["candidate_info"]["position"],
            status=AttemptStatus(attempt["status"]),
            total_tasks=len(attempt["task_ids"]),
            current_task_index=attempt["current_task_index"],
            created_at=attempt["created_at"],
            started_at=attempt.get("started_at"),
            completed_at=attempt.get("completed_at"),
            overall_score=overall_fit.get("score"),
            overall_grade=overall_fit.get("grade"),
        ))
    
    return AttemptListResponse(
        attempts=attempt_list,
        total=total,
        page=page,
        page_size=page_size,
    )


def _attempt_doc_to_response(attempt: dict) -> AttemptResponse:
    """Convert MongoDB document to AttemptResponse."""
    return AttemptResponse(
        id=str(attempt["_id"]),
        token=attempt["token"],
        candidate_info=CandidateInfo(**attempt["candidate_info"]),
        task_ids=attempt["task_ids"],
        status=AttemptStatus(attempt["status"]),
        created_by=attempt["created_by"],
        started_at=attempt.get("started_at"),
        completed_at=attempt.get("completed_at"),
        expires_at=attempt["expires_at"],
        current_task_index=attempt["current_task_index"],
        created_at=attempt["created_at"],
        analysis_result=attempt.get("analysis_result"),
    )


async def get_or_compute_ats_score(attempt_id: str) -> dict:
    """
    Get ATS score for an attempt.
    If already stored in 'ats_result', returns it.
    Otherwise, calculates it from resume_text, stores it, and returns it.
    """
    attempts = get_attempts_collection()
    
    try:
        attempt = await attempts.find_one({"_id": ObjectId(attempt_id)})
    except Exception:
        return None
        
    if not attempt:
        return None

    # 1. Return cached result if exists
    if "ats_result" in attempt:
        return attempt["ats_result"]
        
    # 2. Calculate if missing
    candidate_info = attempt.get("candidate_info", {})
    resume_text = candidate_info.get("resume_text", "")
    
    if not resume_text:
        # Cannot calculate, return empty/zero structure but don't save it as permanent 'result'
        # so that if they upload resume later (unlikely flow but safe), we retry.
        return {
            "ats_score": 0.0,
            "breakdown": {"formatting": 0, "sections": 0, "contact": 0, "content": 0, "length": 0},
            "formatting_issues": [],
            "message": "No resume text found"
        }

    # Calculate
    result = calculate_ats_score(resume_text, "")
    
    # 3. Store result
    await attempts.update_one(
        {"_id": ObjectId(attempt_id)},
        {"$set": {"ats_result": result}}
    )
    
    return result
