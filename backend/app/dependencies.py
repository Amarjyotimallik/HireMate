"""
Dependency Injection for FastAPI

Provides common dependencies like current user, database access, etc.
"""

from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings
from app.core import decode_token, unauthorized
from app.services import get_user_by_id, get_first_active_user
from app.schemas import UserResponse


# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserResponse]:
    """Get current user if authenticated, else None."""
    if not credentials:
        return None
    
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    
    if payload.get("type") != "access":
        return None
    
    user = await get_user_by_id(payload.get("sub"))
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> UserResponse:
    """Get current authenticated user (required). Accepts JWT, or demo token, or dev_mode (no token)."""
    settings = get_settings()
    token = (credentials.credentials or "").strip() if credentials else ""

    # Demo token: Bearer token equals DEMO_AUTH_TOKEN (e.g. "demo") -> use first active user
    if settings.demo_auth_token and token == settings.demo_auth_token:
        dev_user = await get_first_active_user()
        if dev_user:
            return dev_user
        raise unauthorized(
            "Demo token accepted but no active user in database. Run from backend/: python scripts/seed_tasks.py"
        )

    # Dev only: when no Bearer token is provided, use first active user so recruiter APIs can be called without login UI
    if settings.dev_mode and not token:
        dev_user = await get_first_active_user()
        if dev_user:
            return dev_user
        raise unauthorized(
            "DEV_MODE is on but no active user in database. Run from backend/: python scripts/seed_tasks.py"
        )

    if not credentials or not token:
        raise unauthorized(
            "Missing authentication token. Use Authorization: Bearer demo for testing, or set DEV_MODE=true in backend/.env."
        )
    payload = decode_token(credentials.credentials)
    if not payload:
        raise unauthorized("Invalid or expired token")
    if payload.get("type") != "access":
        raise unauthorized("Invalid token type")
    user = await get_user_by_id(payload.get("sub"))
    if not user:
        raise unauthorized("User not found")
    return user


async def get_client_info(request: Request) -> dict:
    """Extract client info from request."""
    return {
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host if request.client else None,
    }
