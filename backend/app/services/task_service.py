"""
Task Service

Handles task CRUD operations.
"""

import random
from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from app.db import get_tasks_collection
from app.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskBrief,
    TaskOption,
)
from app.core import TaskNotFoundError


async def create_task(task_data: TaskCreate, user_id: str) -> TaskResponse:
    """Create a new task."""
    tasks = get_tasks_collection()
    
    now = datetime.utcnow()
    task_doc = {
        "title": task_data.title,
        "description": task_data.description,
        "scenario": task_data.scenario,
        "category": task_data.category.value,
        "difficulty": task_data.difficulty.value,
        "time_limit_seconds": task_data.time_limit_seconds,
        "options": [opt.model_dump() for opt in task_data.options],
        "reasoning_required": task_data.reasoning_required,
        "reasoning_min_length": task_data.reasoning_min_length,
        "created_by": user_id,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    
    result = await tasks.insert_one(task_doc)
    
    return TaskResponse(
        id=str(result.inserted_id),
        **task_data.model_dump(),
        created_by=user_id,
        created_at=now,
        updated_at=now,
        is_active=True,
    )


async def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    """Get a task by ID."""
    tasks = get_tasks_collection()
    
    try:
        task = await tasks.find_one({"_id": ObjectId(task_id)})
    except Exception:
        return None
    
    if not task:
        return None
    
    return _task_doc_to_response(task)


async def get_tasks(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    is_active: bool = True,
) -> TaskListResponse:
    """Get paginated list of tasks."""
    tasks = get_tasks_collection()
    
    # Build query
    query = {"is_active": is_active}
    if category:
        query["category"] = category
    
    # Get total count
    total = await tasks.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * page_size
    cursor = tasks.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    
    task_list = []
    async for task in cursor:
        task_list.append(_task_doc_to_response(task))
    
    return TaskListResponse(
        tasks=task_list,
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_task(task_id: str, task_data: TaskUpdate) -> TaskResponse:
    """Update a task."""
    tasks = get_tasks_collection()
    
    # Get existing task
    existing = await tasks.find_one({"_id": ObjectId(task_id)})
    if not existing:
        raise TaskNotFoundError(f"Task {task_id} not found")
    
    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}
    
    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            if key == "options":
                update_doc["options"] = [opt.model_dump() if hasattr(opt, 'model_dump') else opt for opt in value]
            elif key == "category" or key == "difficulty":
                update_doc[key] = value.value if hasattr(value, 'value') else value
            else:
                update_doc[key] = value
    
    await tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": update_doc}
    )
    
    # Return updated task
    updated = await tasks.find_one({"_id": ObjectId(task_id)})
    return _task_doc_to_response(updated)


async def delete_task(task_id: str) -> bool:
    """Soft delete a task."""
    tasks = get_tasks_collection()
    
    result = await tasks.update_one(
        {"_id": ObjectId(task_id)},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow(),
            }
        }
    )
    
    return result.modified_count > 0


# Position keywords -> task categories (for "questions related to resume")
POSITION_TO_CATEGORIES = {
    "engineer": ["problem_solving", "analytical_thinking", "speed_accuracy"],
    "developer": ["problem_solving", "analytical_thinking", "speed_accuracy"],
    "software": ["problem_solving", "analytical_thinking"],
    "designer": ["communication", "analytical_thinking"],
    "ux": ["communication", "analytical_thinking"],
    "ui": ["communication", "analytical_thinking"],
    "manager": ["decision_confidence", "communication"],
    "lead": ["decision_confidence", "communication", "problem_solving"],
    "analyst": ["analytical_thinking", "decision_confidence"],
    "product": ["decision_confidence", "communication"],
    "data": ["analytical_thinking", "problem_solving"],
    "qa": ["analytical_thinking", "speed_accuracy"],
    "devops": ["problem_solving", "speed_accuracy"],
}


async def get_suggested_task_ids(position: Optional[str], limit: int = 10) -> List[str]:
    """
    Suggest task IDs based on parsed position so assessment questions relate to the resume.
    Maps position keywords to task categories and returns active task IDs.
    """
    if not position or not position.strip():
        # No position: return first N active tasks
        result = await get_tasks(page=1, page_size=limit)
        return [t.id for t in result.tasks]
    pos_lower = position.lower()
    categories = set()
    for keyword, cats in POSITION_TO_CATEGORIES.items():
        if keyword in pos_lower:
            categories.update(cats)
    if not categories:
        result = await get_tasks(page=1, page_size=limit)
        return [t.id for t in result.tasks]
    tasks_coll = get_tasks_collection()
    cursor = tasks_coll.find(
        {"is_active": True, "category": {"$in": list(categories)}}
    ).limit(limit).sort("created_at", -1)
    ids = []
    async for task in cursor:
        ids.append(str(task["_id"]))
    return ids


async def get_tasks_by_ids(task_ids: List[str]) -> List[TaskBrief]:
    """Get multiple tasks by IDs for assessment."""
    tasks = get_tasks_collection()
    
    object_ids = [ObjectId(tid) for tid in task_ids]
    cursor = tasks.find({"_id": {"$in": object_ids}, "is_active": True})
    
    result = []
    async for task in cursor:
        # Shuffle options so correct answer isn't always in same position
        shuffled_options = task["options"].copy()
        random.shuffle(shuffled_options)
        
        result.append(TaskBrief(
            id=str(task["_id"]),
            title=task["title"],
            scenario=task["scenario"],
            category=task["category"],
            difficulty=task["difficulty"],
            options=[TaskOption(**opt) for opt in shuffled_options],
            reasoning_required=task["reasoning_required"],
            reasoning_min_length=task["reasoning_min_length"],
            time_limit_seconds=task.get("time_limit_seconds"),
        ))
    
    # Sort by original order
    id_to_task = {t.id: t for t in result}
    return [id_to_task[tid] for tid in task_ids if tid in id_to_task]


def _task_doc_to_response(task: dict) -> TaskResponse:
    """Convert MongoDB document to TaskResponse."""
    return TaskResponse(
        id=str(task["_id"]),
        title=task["title"],
        description=task.get("description"),
        scenario=task["scenario"],
        category=task["category"],
        difficulty=task["difficulty"],
        time_limit_seconds=task.get("time_limit_seconds"),
        options=[TaskOption(**opt) for opt in task["options"]],
        reasoning_required=task["reasoning_required"],
        reasoning_min_length=task["reasoning_min_length"],
        created_by=task["created_by"],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        is_active=task["is_active"],
    )
