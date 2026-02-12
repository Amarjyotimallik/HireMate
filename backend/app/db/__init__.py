"""
Database package
"""

from app.db.mongodb import (
    connect_to_mongodb,
    close_mongodb_connection,
    get_database,
    get_users_collection,
    get_tasks_collection,
    get_attempts_collection,
    get_events_collection,
    get_metrics_collection,
    get_skills_collection,
)

__all__ = [
    "connect_to_mongodb",
    "close_mongodb_connection",
    "get_database",
    "get_users_collection",
    "get_tasks_collection",
    "get_attempts_collection",
    "get_events_collection",
    "get_metrics_collection",
    "get_skills_collection",
]
