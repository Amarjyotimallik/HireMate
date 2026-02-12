"""
ML Anomaly Detection API Endpoint
Provides ML-based behavioral anomaly scoring for candidates.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from bson import ObjectId

from app.dependencies import get_current_user
from app.schemas import UserResponse
from app.db import get_events_collection, get_attempts_collection
from app.services.ml_anomaly_service import get_ml_behavior_report

router = APIRouter(prefix="/ml-anomaly", tags=["ML Anomaly Detection"])


@router.get("/{attempt_id}")
async def get_ml_anomaly_score(
    attempt_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict:
    """
    Get ML-based behavioral anomaly score for a candidate.
    
    This uses a trained Isolation Forest model to detect behavioral patterns
    that deviate from typical independent problem-solving.
    """
    # Verify attempt exists and belongs to recruiter
    attempts_coll = get_attempts_collection()
    attempt = await attempts_coll.find_one({"_id": ObjectId(attempt_id)})
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if str(attempt.get("created_by")) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get events
    events_coll = get_events_collection()
    cursor = events_coll.find({
        "$or": [
            {"attempt_id": attempt_id},
            {"attempt_id": ObjectId(attempt_id)}
        ]
    }).sort("sequence_number", 1)
    events = await cursor.to_list(length=10000)
    
    # Get candidate name
    candidate_name = attempt.get("candidate_info", {}).get("name", "Candidate")
    
    # Get ML report
    report = await get_ml_behavior_report(events, candidate_name)
    
    return {
        "attempt_id": attempt_id,
        "candidate_name": candidate_name,
        "ml_anomaly_report": report,
        "status": "success"
    }
