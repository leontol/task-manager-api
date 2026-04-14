from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.schemas import TaskCreate, TaskUpdate, TaskStatusEnum, TaskPriorityEnum
from app.repositories.task_repository import TaskRepository

class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository
    
    async def create_task(self, task_data: TaskCreate) -> Dict[str, Any]:
        """Бизнес-логика создания задачи"""
        if task_data.priority == TaskPriorityEnum.HIGH and not task_data.description:
            raise ValueError("Для задач с высоким приоритетом обязательно описание")
        
        return await self.repository.create(task_data)
    
    async def get_tasks(
        self,
        status: Optional[TaskStatusEnum] = None,
        priority: Optional[TaskPriorityEnum] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Dict[str, Any]], int]:
        """Получение задач с фильтрацией"""
        if skip < 0:
            skip = 0
        if limit < 1 or limit > 100:
            limit = 10
        
        return await self.repository.get_filtered(status, priority, skip, limit)
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получение задачи по ID"""
        return await self.repository.get(task_id)
    
    async def get_task_stats(self) -> Dict[str, int]:
        """Получение статистики по задачам"""
        return await self.repository.get_stats_by_status()
    
    async def update_task(self, task_id: str, task_data: TaskUpdate) -> Dict[str, Any]:
        """Обновление задачи"""
        task = await self.repository.get(task_id)
        if not task:
            raise ValueError("Задача не найдена")
        
        if task["status"] == "completed" and task_data.status and task_data.status != TaskStatusEnum.COMPLETED:
            raise ValueError("Нельзя изменить статус выполненной задачи")
        
        return await self.repository.update(task_id, task_data)
    
    async def delete_task(self, task_id: str) -> bool:
        """Удаление задачи"""
        task = await self.repository.get(task_id)
        if not task:
            raise ValueError("Задача не найдена")
        
        return await self.repository.delete(task_id)