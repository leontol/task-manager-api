import pytest
from app.services.task_service import TaskService
from app.repositories.task_repository import TaskRepository
from app.models.schemas import TaskCreate, TaskStatusEnum, TaskPriorityEnum


class TestTaskService:
    """Тесты для TaskService"""
    
    def setup_method(self):
        """Очищает хранилище перед каждым тестом"""
        TaskRepository.clear()
    
    @pytest.mark.asyncio
    async def test_create_task(self):
        service = TaskService(TaskRepository())
        task_data = TaskCreate(
            title="Test Task",
            description="Test Description",
            status=TaskStatusEnum.PENDING,
            priority=TaskPriorityEnum.MEDIUM
        )
        
        task = await service.create_task(task_data)
        
        assert task["title"] == "Test Task"
        assert task["status"] == "pending"
        assert "id" in task
    
    @pytest.mark.asyncio
    async def test_create_task_high_priority_no_description(self):
        service = TaskService(TaskRepository())
        task_data = TaskCreate(
            title="Test Task",
            description=None,
            status=TaskStatusEnum.PENDING,
            priority=TaskPriorityEnum.HIGH
        )
        
        with pytest.raises(ValueError, match="Для задач с высоким приоритетом обязательно описание"):
            await service.create_task(task_data)
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_filters(self):
        service = TaskService(TaskRepository())
        
        await service.create_task(TaskCreate(
            title="Task 1", 
            description="Description 1",
            status=TaskStatusEnum.PENDING, 
            priority=TaskPriorityEnum.HIGH
        ))
        await service.create_task(TaskCreate(
            title="Task 2", 
            description="Description 2",
            status=TaskStatusEnum.COMPLETED, 
            priority=TaskPriorityEnum.LOW
        ))
        
        tasks, total = await service.get_tasks(status=TaskStatusEnum.PENDING)
        assert total == 1
        assert tasks[0]["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_get_tasks_pagination(self):
        service = TaskService(TaskRepository())
        
        for i in range(5):
            await service.create_task(TaskCreate(
                title=f"Task {i}", 
                description=f"Description {i}",
                status=TaskStatusEnum.PENDING, 
                priority=TaskPriorityEnum.MEDIUM
            ))
        
        tasks, total = await service.get_tasks(skip=0, limit=2)
        assert len(tasks) == 2
        assert total == 5
        
        tasks, total = await service.get_tasks(skip=2, limit=2)
        assert len(tasks) == 2
    
    @pytest.mark.asyncio
    async def test_get_task_stats(self):
        service = TaskService(TaskRepository())
        
        await service.create_task(TaskCreate(
            title="Pending", 
            description="Desc",
            status=TaskStatusEnum.PENDING, 
            priority=TaskPriorityEnum.MEDIUM
        ))
        await service.create_task(TaskCreate(
            title="Completed", 
            description="Desc",
            status=TaskStatusEnum.COMPLETED, 
            priority=TaskPriorityEnum.MEDIUM
        ))
        
        stats = await service.get_task_stats()
        
        assert stats.get("pending") == 1
        assert stats.get("completed") == 1