from fastapi import Depends, HTTPException, status
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService
from app.core.database import db_manager

async def get_task_repository():
    """Dependency для получения репозитория"""
    async with db_manager.get_connection() as conn:
        return TaskRepository(conn)

async def get_task_service(
    repository: TaskRepository = Depends(get_task_repository)
) -> TaskService:
    return TaskService(repository)

async def get_task_by_id(
    task_id: str,
    repository: TaskRepository = Depends(get_task_repository)
) -> dict:
    task = await repository.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена"
        )
    return task

async def task_exists(
    task_id: str,
    repository: TaskRepository = Depends(get_task_repository)
) -> bool:
    task = await repository.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена"
        )
    return True