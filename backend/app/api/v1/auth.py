"""
Authentication API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefresh,
)
from app.services import create_user, authenticate_user, refresh_tokens
from app.dependencies import get_current_user
from app.core import InvalidCredentialsError, InvalidTokenError


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new recruiter account.
    """
    try:
        user = await create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Authenticate and receive JWT tokens.
    """
    try:
        tokens = await authenticate_user(credentials.email, credentials.password)
        return tokens
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(token_data: TokenRefresh):
    """
    Refresh access token using refresh token.
    """
    try:
        tokens = await refresh_tokens(token_data.refresh_token)
        return tokens
    except (InvalidTokenError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user info.
    """
    return current_user
