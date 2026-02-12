"""
Tasks API Endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    UserResponse,
)
from app.services import create_task, get_task_by_id, get_tasks, update_task, delete_task
from app.dependencies import get_current_user
from app.core import TaskNotFoundError


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_data: TaskCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Create a new assessment task.
    
    Tasks contain micro decision-making scenarios with multiple options.
    Each option has a risk level (low/medium/high) for behavioral analysis.
    """
    task = await create_task(task_data, current_user.id)
    return task


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    include_inactive: bool = False,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get paginated list of tasks.
    """
    result = await get_tasks(
        page=page,
        page_size=page_size,
        category=category,
        is_active=not include_inactive,
    )
    return result


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get a specific task by ID.
    """
    task = await get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_existing_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Update a task.
    """
    try:
        task = await update_task(task_id, task_data)
        return task
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Soft delete a task (marks as inactive).
    """
    success = await delete_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
