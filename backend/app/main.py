"""
HireMate Backend - Main Application

Behavior-based skill observation system for candidate assessment.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import connect_to_mongodb, close_mongodb_connection, get_database
from app.db.indexes import create_indexes
from app.api import v1_router
from app.api.websocket import handle_assessment_websocket, handle_live_monitoring_websocket
from app.services.bulk_assessment_service import check_celery_available


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await connect_to_mongodb()
    
    # Create indexes
    db = get_database()
    await create_indexes(db)
    
    # Log DEV_MODE so it's clear when testing without login
    s = get_settings()
    if s.dev_mode:
        print("[OK] DEV_MODE=true - recruiter APIs accept requests without JWT (first active user)")
    else:
        print("[i] DEV_MODE=false - recruiter APIs require JWT (Authorization: Bearer <token>)")
    
    # Check Redis/Celery availability for bulk processing
    check_celery_available()
    
    yield
    
    # Shutdown
    await close_mongodb_connection()


# Initialize FastAPI app
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    HireMate Backend API - Behavior-Based Skill Observation System
    
    ## Overview
    This API powers the HireMate assessment platform, which observes HOW candidates 
    solve micro decision-making tasks to generate explainable skill profiles.
    
    ## Key Features
    - **Behavioral Event Logging**: Append-only event stream capturing all interactions
    - **Real-time WebSockets**: Live event broadcasting for active assessments
    - **Post-hoc Metrics**: Behavioral metrics computed after task completion
    - **Deterministic Skills**: Rule-based skill interpretation (no ML black boxes)
    
    ## Authentication
    - **Recruiters**: JWT Bearer tokens
    - **Candidates**: One-time assessment tokens
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
cors_origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(v1_router)


# WebSocket endpoints
@app.websocket("/ws/assessment/{token}")
async def websocket_assessment(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for candidate assessments.
    
    Candidates connect here to log behavioral events in real-time.
    """
    await handle_assessment_websocket(websocket, token)


@app.websocket("/ws/live/{attempt_id}")
async def websocket_live_monitoring(websocket: WebSocket, attempt_id: str):
    """
    WebSocket endpoint for recruiter live monitoring.
    
    Recruiters can watch assessment progress in real-time.
    Requires JWT authentication via query param: ?token=<jwt>
    """
    await handle_live_monitoring_websocket(websocket, attempt_id)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
