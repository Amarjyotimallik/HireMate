"""
Custom Exceptions for HireMate Backend
"""

from fastapi import HTTPException, status


class HireMateException(Exception):
    """Base exception for HireMate."""
    pass


# Authentication Exceptions
class InvalidCredentialsError(HireMateException):
    """Invalid username or password."""
    pass


class TokenExpiredError(HireMateException):
    """Token has expired."""
    pass


class InvalidTokenError(HireMateException):
    """Token is invalid."""
    pass


class TokenAlreadyUsedError(HireMateException):
    """One-time token has already been used."""
    pass


# Assessment Exceptions
class AttemptNotFoundError(HireMateException):
    """Assessment attempt not found."""
    pass


class AttemptLockedError(HireMateException):
    """Assessment attempt is locked."""
    pass


class AttemptExpiredError(HireMateException):
    """Assessment attempt has expired."""
    pass


class InvalidEventError(HireMateException):
    """Behavior event is invalid."""
    pass


class InvalidStateTransitionError(HireMateException):
    """Invalid state transition for event."""
    pass


# Task Exceptions
class TaskNotFoundError(HireMateException):
    """Task not found."""
    pass


# HTTP Exception shortcuts
def unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden(detail: str = "Access denied") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def not_found(detail: str = "Resource not found") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
    )


def bad_request(detail: str = "Bad request") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def conflict(detail: str = "Conflict") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )


def unprocessable(detail: str = "Unprocessable entity") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail,
    )
