"""
Event Service

Handles behavior event logging, validation, and retrieval.
This is the core of the behavioral observation system.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from bson import ObjectId

from app.db import get_events_collection, get_attempts_collection, get_tasks_collection
from app.schemas import (
    EventCreate,
    EventBatchCreate,
    EventResponse,
    EventListResponse,
    EventType,
    AttemptStatus,
)
from app.core import (
    InvalidEventError,
    InvalidStateTransitionError,
    AttemptNotFoundError,
    AttemptLockedError,
    hash_ip,
)


# Valid state transitions for event state machine
VALID_TRANSITIONS = {
    None: [EventType.TASK_STARTED],
    EventType.TASK_STARTED: [
        EventType.OPTION_VIEWED,
        EventType.OPTION_SELECTED,
        EventType.REASONING_STARTED,
        EventType.IDLE_DETECTED,
        EventType.FOCUS_LOST,
    ],
    EventType.OPTION_VIEWED: [
        EventType.OPTION_VIEWED,
        EventType.OPTION_SELECTED,
        EventType.REASONING_STARTED,
        EventType.IDLE_DETECTED,
        EventType.FOCUS_LOST,
        EventType.FOCUS_GAINED,
    ],
    EventType.OPTION_SELECTED: [
        EventType.OPTION_CHANGED,
        EventType.OPTION_VIEWED,
        EventType.REASONING_STARTED,
        EventType.TASK_COMPLETED,
        EventType.IDLE_DETECTED,
        EventType.FOCUS_LOST,
        EventType.FOCUS_GAINED,
    ],
    EventType.OPTION_CHANGED: [
        EventType.OPTION_CHANGED,
        EventType.OPTION_VIEWED,
        EventType.REASONING_STARTED,
        EventType.TASK_COMPLETED,
        EventType.IDLE_DETECTED,
        EventType.FOCUS_LOST,
        EventType.FOCUS_GAINED,
    ],
    EventType.REASONING_STARTED: [
        EventType.REASONING_UPDATED,
        EventType.REASONING_SUBMITTED,
        EventType.OPTION_VIEWED,
        EventType.OPTION_CHANGED,
        EventType.IDLE_DETECTED,
        EventType.FOCUS_LOST,
        EventType.FOCUS_GAINED,
    ],
    EventType.REASONING_UPDATED: [
        EventType.REASONING_UPDATED,
        EventType.REASONING_SUBMITTED,
        EventType.OPTION_VIEWED,
        EventType.OPTION_CHANGED,
        EventType.IDLE_DETECTED,
        EventType.FOCUS_LOST,
        EventType.FOCUS_GAINED,
    ],
    EventType.REASONING_SUBMITTED: [
        EventType.TASK_COMPLETED,
        EventType.OPTION_VIEWED,
        EventType.OPTION_CHANGED,
        EventType.IDLE_DETECTED,
        EventType.FOCUS_LOST,
        EventType.FOCUS_GAINED,
    ],
    EventType.TASK_COMPLETED: [
        EventType.TASK_STARTED,  # Next task
    ],
    EventType.IDLE_DETECTED: [
        EventType.OPTION_VIEWED,
        EventType.OPTION_SELECTED,
        EventType.OPTION_CHANGED,
        EventType.REASONING_STARTED,
        EventType.REASONING_UPDATED,
        EventType.FOCUS_LOST,
        EventType.FOCUS_GAINED,
    ],
    EventType.FOCUS_LOST: [
        EventType.FOCUS_GAINED,
        EventType.IDLE_DETECTED,
    ],
    EventType.FOCUS_GAINED: [
        EventType.OPTION_VIEWED,
        EventType.OPTION_SELECTED,
        EventType.OPTION_CHANGED,
        EventType.REASONING_STARTED,
        EventType.REASONING_UPDATED,
        EventType.REASONING_SUBMITTED,
        EventType.TASK_COMPLETED,
        EventType.IDLE_DETECTED,
        EventType.FOCUS_LOST,
    ],
}


async def log_event(
    attempt_id: str,
    event_data: EventCreate,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> EventResponse:
    """Log a single behavior event."""
    events = get_events_collection()
    attempts = get_attempts_collection()
    
    # Validate attempt exists and is in progress
    attempt = await attempts.find_one({"_id": ObjectId(attempt_id)})
    if not attempt:
        raise AttemptNotFoundError("Assessment not found")
    
    if attempt["status"] != AttemptStatus.IN_PROGRESS.value:
        raise AttemptLockedError("Assessment is not in progress")
    
    # Validate task belongs to attempt
    if event_data.task_id not in attempt["task_ids"]:
        raise InvalidEventError(f"Task {event_data.task_id} not in assessment")
    
    # Get last event for this attempt/task to validate state transition
    last_event = await events.find_one(
        {"attempt_id": attempt_id, "task_id": event_data.task_id},
        sort=[("sequence_number", -1)]
    )
    
    # Validate state transition (relaxed for now - can be made strict)
    last_event_type = EventType(last_event["event_type"]) if last_event else None
    
    # Note: State validation is important but we allow some flexibility
    # to not lose events due to race conditions
    
    # Get next sequence number
    last_any_event = await events.find_one(
        {"attempt_id": attempt_id},
        sort=[("sequence_number", -1)]
    )
    sequence_number = (last_any_event["sequence_number"] + 1) if last_any_event else 1
    
    # Create event document (server-side timestamp is authoritative)
    now = datetime.utcnow()
    event_doc = {
        "attempt_id": attempt_id,
        "task_id": event_data.task_id,
        "event_type": event_data.event_type.value,
        "timestamp": now,
        "sequence_number": sequence_number,
        "payload": event_data.payload,
        "client_timestamp": event_data.client_timestamp,
        "metadata": {
            "user_agent": user_agent,
            "ip_hash": hash_ip(ip_address) if ip_address else None,
        }
    }
    
    result = await events.insert_one(event_doc)
    
    return EventResponse(
        id=str(result.inserted_id),
        attempt_id=attempt_id,
        task_id=event_data.task_id,
        event_type=event_data.event_type,
        timestamp=now,
        sequence_number=sequence_number,
        payload=event_data.payload,
        client_timestamp=event_data.client_timestamp,
    )


async def log_events_batch(
    attempt_id: str,
    events_data: EventBatchCreate,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> List[EventResponse]:
    """Log multiple behavior events in batch."""
    results = []
    
    for event_data in events_data.events:
        result = await log_event(
            attempt_id=attempt_id,
            event_data=event_data,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        results.append(result)
    
    return results


async def get_events_for_attempt(
    attempt_id: str,
    task_id: Optional[str] = None,
    event_type: Optional[str] = None,
) -> EventListResponse:
    """Get all events for an attempt."""
    events = get_events_collection()
    
    query = {"attempt_id": attempt_id}
    if task_id:
        query["task_id"] = task_id
    if event_type:
        query["event_type"] = event_type
    
    cursor = events.find(query).sort("sequence_number", 1)
    
    event_list = []
    async for event in cursor:
        event_list.append(EventResponse(
            id=str(event["_id"]),
            attempt_id=event["attempt_id"],
            task_id=event["task_id"],
            event_type=EventType(event["event_type"]),
            timestamp=event["timestamp"],
            sequence_number=event["sequence_number"],
            payload=event["payload"],
            client_timestamp=event.get("client_timestamp"),
        ))
    
    return EventListResponse(
        events=event_list,
        total=len(event_list),
    )


async def get_events_for_task(attempt_id: str, task_id: str) -> List[EventResponse]:
    """Get events for a specific task within an attempt."""
    result = await get_events_for_attempt(attempt_id, task_id=task_id)
    return result.events


async def validate_option_id(task_id: str, option_id: str) -> bool:
    """Validate that an option ID exists in a task."""
    tasks = get_tasks_collection()
    
    task = await tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        return False
    
    option_ids = [opt["id"] for opt in task["options"]]
    return option_id in option_ids
