"""
Test Configuration

Shared fixtures and configuration for pytest.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator

from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.config import get_settings
from app.db import db


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create a test database connection."""
    settings = get_settings()
    
    # Use a separate test database
    test_db_name = f"{settings.mongodb_database}_test"
    
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[test_db_name]
    
    # Set the test database
    db.client = client
    db.database = database
    
    yield database
    
    # Cleanup: drop test database
    await client.drop_database(test_db_name)
    client.close()


@pytest.fixture
async def client(test_db) -> AsyncGenerator:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Create auth headers with a valid JWT token."""
    # Register a test user
    register_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "role": "recruiter",
    }
    
    await client.post("/api/v1/auth/register", json=register_data)
    
    # Login to get token
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    tokens = response.json()
    
    return {"Authorization": f"Bearer {tokens['access_token']}"}
