"""
API v1 Router

Aggregates all v1 API endpoints.
"""

from fastapi import APIRouter

from app.api.v1 import auth, tasks, attempts, assessment, events, metrics, skills, dashboard, live_assessment, resume, outcomes, email, kiwi, bulk, ml_anomaly, predictions


router = APIRouter(prefix="/api/v1")

# Include all routers
router.include_router(auth.router)
router.include_router(tasks.router)
router.include_router(attempts.router)
router.include_router(assessment.router)
router.include_router(events.router)
router.include_router(metrics.router)
router.include_router(skills.router)
router.include_router(dashboard.router)
router.include_router(live_assessment.router)
router.include_router(resume.router)
router.include_router(outcomes.router)
router.include_router(email.router)
router.include_router(kiwi.router)
router.include_router(bulk.router)
router.include_router(ml_anomaly.router)
router.include_router(predictions.router)
