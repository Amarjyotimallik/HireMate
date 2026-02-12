"""
MongoDB Database Connection

Provides async MongoDB client using Motor.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from app.config import get_settings


class MongoDB:
    """MongoDB connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


db = MongoDB()


async def connect_to_mongodb():
    """Connect to MongoDB on application startup."""
    settings = get_settings()
    
    db.client = AsyncIOMotorClient(
        settings.mongodb_url,
        maxPoolSize=50,
        minPoolSize=10,
    )
    db.database = db.client[settings.mongodb_database]
    
    # Verify connection
    await db.client.admin.command("ping")
    print(f"[OK] Connected to MongoDB: {settings.mongodb_database}")


async def close_mongodb_connection():
    """Close MongoDB connection on application shutdown."""
    if db.client:
        db.client.close()
        print("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    if db.database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb first.")
    return db.database


# Collection accessors
def get_users_collection():
    """Get users collection."""
    return get_database().users


def get_tasks_collection():
    """Get tasks collection."""
    return get_database().tasks


def get_attempts_collection():
    """Get task_attempts collection."""
    return get_database().task_attempts


def get_events_collection():
    """Get behavior_events collection."""
    return get_database().behavior_events


def get_metrics_collection():
    """Get computed_metrics collection."""
    return get_database().computed_metrics


def get_skills_collection():
    """Get skill_profiles collection."""
    return get_database().skill_profiles
