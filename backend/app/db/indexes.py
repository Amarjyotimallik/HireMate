"""
MongoDB Index Definitions

Creates indexes for optimal query performance.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase


async def create_indexes(database: AsyncIOMotorDatabase):
    """Create all required indexes."""
    
    # Users collection
    await database.users.create_index("email", unique=True)
    await database.users.create_index("is_active")
    
    # Tasks collection
    await database.tasks.create_index("is_active")
    await database.tasks.create_index("category")
    await database.tasks.create_index("created_by")
    
    # Task attempts collection
    await database.task_attempts.create_index("token", unique=True)
    await database.task_attempts.create_index("status")
    await database.task_attempts.create_index("created_by")
    await database.task_attempts.create_index("candidate_info.email")
    await database.task_attempts.create_index([("expires_at", 1)])
    
    # Behavior events collection (most critical for performance)
    await database.behavior_events.create_index(
        [("attempt_id", 1), ("sequence_number", 1)],
        unique=True
    )
    await database.behavior_events.create_index(
        [("attempt_id", 1), ("task_id", 1), ("timestamp", 1)]
    )
    await database.behavior_events.create_index(
        [("event_type", 1), ("timestamp", -1)]
    )
    await database.behavior_events.create_index("attempt_id")
    
    # Computed metrics collection
    await database.computed_metrics.create_index("attempt_id", unique=True)
    
    # Skill profiles collection
    await database.skill_profiles.create_index("attempt_id", unique=True)
    
    print("[OK] All indexes created successfully")
