from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Security
from app.models.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, 
    TaskStatusEnum, TaskPriorityEnum, 
    PaginationMeta, TaskListResponse, TaskStatsResponse
)
from app.services.task_service import TaskService
from app.api.dependencies.tasks import get_task_service, get_task_by_id, task_exists
from app.api.dependencies.auth import verify_api_key  # Добавляем импорт

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    service: TaskService = Depends(get_task_service),
    api_key: str = Security(verify_api_key)  # Защита
):
    """Создание новой задачи (требуется API Key)"""
    try:
        task = await service.create_task(task_data)
        return TaskResponse(**task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/stats", response_model=TaskStatsResponse)
async def get_tasks_stats(
    service: TaskService = Depends(get_task_service),
    api_key: str = Security(verify_api_key)  # Защита
):
    """Получение статистики по задачам (требуется API Key)"""
    stats = await service.get_task_stats()
    total = sum(stats.values())
    
    return TaskStatsResponse(
        pending=stats.get("pending", 0),
        in_progress=stats.get("in_progress", 0),
        completed=stats.get("completed", 0),
        total=total
    )


@router.get("/tasks", response_model=TaskListResponse)
async def get_all_tasks(
    service: TaskService = Depends(get_task_service),
    api_key: str = Security(verify_api_key),  # Защита
    status: Optional[TaskStatusEnum] = Query(None, description="Фильтр по статусу"),
    priority: Optional[TaskPriorityEnum] = Query(None, description="Фильтр по приоритету"),
    skip: int = Query(0, ge=0, description="Сколько задач пропустить"),
    limit: int = Query(10, ge=1, le=100, description="Максимум задач на странице")
):
    """Получение списка задач с фильтрацией и пагинацией (требуется API Key)"""
    tasks, total_count = await service.get_tasks(status, priority, skip, limit)
    
    tasks_response = [TaskResponse(**task) for task in tasks]
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return TaskListResponse(
        data=tasks_response,
        meta=PaginationMeta(
            total_count=total_count,
            page=page,
            page_size=limit
        )
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task: dict = Depends(get_task_by_id),
    api_key: str = Security(verify_api_key)  # Защита
):
    """Получение задачи по ID (требуется API Key)"""
    return TaskResponse(**task)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
    task_id: str = None,
    task_exists: bool = Depends(task_exists),
    api_key: str = Security(verify_api_key)  # Защита
):
    """Обновление задачи (требуется API Key)"""
    try:
        updated = await service.update_task(task_id, task_data)
        return TaskResponse(**updated)
    except ValueError as e:
        if "не найдена" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    service: TaskService = Depends(get_task_service),
    task_id: str = None,
    task_exists: bool = Depends(task_exists),
    api_key: str = Security(verify_api_key)  # Защита
):
    """Удаление задачи (требуется API Key)"""
    try:
        await service.delete_task(task_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))