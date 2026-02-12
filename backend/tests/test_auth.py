"""
Tests for Authentication

Validates user registration, login, and token management.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    async def test_register_user(self, client: AsyncClient, test_db):
        """Test user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "securepassword123",
                "role": "recruiter",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_db):
        """Test that duplicate emails are rejected."""
        # First registration
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "full_name": "First User",
                "password": "password123",
                "role": "recruiter",
            }
        )
        
        # Second registration with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "full_name": "Second User",
                "password": "password456",
                "role": "recruiter",
            }
        )
        
        assert response.status_code == 409

    async def test_login_success(self, client: AsyncClient, test_db):
        """Test successful login."""
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "full_name": "Login Test",
                "password": "testpass123",
                "role": "recruiter",
            }
        )
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "testpass123",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_password(self, client: AsyncClient, test_db):
        """Test login with wrong password."""
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "full_name": "Wrong Pass",
                "password": "correctpass",
                "role": "recruiter",
            }
        )
        
        # Login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongpassword",
            }
        )
        
        assert response.status_code == 401

    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers):
        """Test getting current user info when authenticated."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    async def test_get_me_unauthenticated(self, client: AsyncClient, test_db):
        """Test getting current user info without authentication."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
