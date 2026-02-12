"""
Dashboard API Endpoints
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from app.schemas import UserResponse
from app.dependencies import get_current_user
from app.db import get_attempts_collection, get_events_collection


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get dashboard statistics for the recruiter.
    """
    attempts = get_attempts_collection()
    
    # Get counts
    total_candidates = await attempts.count_documents({"created_by": current_user.id})
    active_assessments = await attempts.count_documents({
        "status": "in_progress",
        "created_by": current_user.id
    })
    
    # Completed today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    completed_today = await attempts.count_documents({
        "status": "completed",
        "completed_at": {"$gte": today_start},
        "created_by": current_user.id
    })
    
    # Completed total
    total_completed = await attempts.count_documents({
        "status": "completed",
        "created_by": current_user.id
    })
    
    # Completion rate
    started = await attempts.count_documents({
        "status": {"$in": ["in_progress", "completed", "locked"]},
        "created_by": current_user.id
    })
    completion_rate = (total_completed / started * 100) if started > 0 else 0
    
    return {
        "total_candidates": total_candidates,
        "active_assessments": active_assessments,
        "completed_today": completed_today,
        "total_completed": total_completed,
        "completion_rate": round(completion_rate, 1),
    }


@router.get("/activity")
async def get_recent_activity(
    limit: int = 10,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get recent activity feed.
    """
    attempts = get_attempts_collection()
    
    # Get recent attempts with activity
    cursor = attempts.find({"created_by": current_user.id}).sort("updated_at", -1).limit(limit)
    
    activities = []
    async for attempt in cursor:
        status = attempt["status"]
        
        if status == "completed":
            action = "Completed Assessment"
            activity_type = "success"
            timestamp = attempt.get("completed_at", attempt["updated_at"])
        elif status == "in_progress":
            action = "Started Assessment"
            activity_type = "info"
            timestamp = attempt.get("started_at", attempt["updated_at"])
        elif status == "pending":
            action = "Assessment Created"
            activity_type = "info"
            timestamp = attempt["created_at"]
        else:
            action = f"Status: {status}"
            activity_type = "warning"
            timestamp = attempt["updated_at"]
        
        # Calculate relative time
        delta = datetime.utcnow() - timestamp
        if delta < timedelta(hours=1):
            relative_time = f"{int(delta.total_seconds() / 60)} minutes ago"
        elif delta < timedelta(days=1):
            relative_time = f"{int(delta.total_seconds() / 3600)} hours ago"
        else:
            relative_time = f"{delta.days} days ago"
        
        activities.append({
            "id": str(attempt["_id"]),
            "candidate_name": attempt["candidate_info"]["name"],
            "action": action,
            "timestamp": relative_time,
            "type": activity_type,
        })
    
    return {"activities": activities}
