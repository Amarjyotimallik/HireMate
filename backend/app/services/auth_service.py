"""
Authentication Service

Handles user registration, login, and token management.
"""

from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.core import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
)
from app.db import get_users_collection
from app.schemas import UserCreate, UserResponse, UserInDB, TokenResponse


async def create_user(user_data: UserCreate) -> UserResponse:
    """Create a new user."""
    users = get_users_collection()
    
    # Check if email already exists
    existing = await users.find_one({"email": user_data.email})
    if existing:
        raise ValueError("Email already registered")
    
    # Create user document
    now = datetime.utcnow()
    user_doc = {
        "email": user_data.email,
        "full_name": user_data.full_name,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role.value,
        "organization_id": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    
    result = await users.insert_one(user_doc)
    
    return UserResponse(
        id=str(result.inserted_id),
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True,
        created_at=now,
    )


async def authenticate_user(email: str, password: str) -> TokenResponse:
    """Authenticate a user and return tokens."""
    users = get_users_collection()
    
    user = await users.find_one({"email": email})
    if not user:
        raise InvalidCredentialsError("Invalid email or password")
    
    if not verify_password(password, user["password_hash"]):
        raise InvalidCredentialsError("Invalid email or password")
    
    if not user.get("is_active", True):
        raise InvalidCredentialsError("Account is disabled")
    
    # Create tokens
    token_data = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def refresh_tokens(refresh_token: str) -> TokenResponse:
    """Refresh access token using refresh token."""
    payload = decode_token(refresh_token)
    
    if not payload:
        raise InvalidTokenError("Invalid refresh token")
    
    if payload.get("type") != "refresh":
        raise InvalidTokenError("Invalid token type")
    
    # Verify user still exists and is active
    users = get_users_collection()
    user = await users.find_one({"_id": ObjectId(payload["sub"])})
    
    if not user or not user.get("is_active", True):
        raise InvalidTokenError("User not found or disabled")
    
    # Create new tokens
    token_data = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
    }
    
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


async def get_user_by_id(user_id: str) -> Optional[UserResponse]:
    """Get user by ID."""
    users = get_users_collection()
    
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    
    if not user:
        return None
    
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user.get("is_active", True),
        created_at=user["created_at"],
    )


async def get_first_active_user() -> Optional[UserResponse]:
    """Get first active user (for dev mode when no JWT is provided)."""
    users = get_users_collection()
    user = await users.find_one({"is_active": True})
    if not user:
        return None
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user.get("is_active", True),
        created_at=user["created_at"],
    )


async def get_current_user_from_token(token: str) -> Optional[UserResponse]:
    """Extract and validate user from JWT token."""
    payload = decode_token(token)
    
    if not payload:
        return None
    
    if payload.get("type") != "access":
        return None
    
    return await get_user_by_id(payload.get("sub"))
