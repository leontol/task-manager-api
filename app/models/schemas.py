from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.models.enums import TaskStatusEnum, TaskPriorityEnum

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    status: TaskStatusEnum = Field(default=TaskStatusEnum.PENDING)
    priority: TaskPriorityEnum = Field(default=TaskPriorityEnum.MEDIUM)

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError('Название задачи не может быть пустым')
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    status: Optional[TaskStatusEnum] = Field(None)
    priority: Optional[TaskPriorityEnum] = Field(None)

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: Optional[str]):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Название задачи не может быть пустым')
        return v

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatusEnum
    priority: TaskPriorityEnum
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class TaskReorder(BaseModel):
    task_ids: List[str]

    @field_validator('task_ids')
    @classmethod
    def check_unique(cls, v: List[str]):
        if len(v) != len(set(v)):
            raise ValueError('ID задач должны быть уникальными')
        return v

class TaskDelete(BaseModel):
    task_id: str = Field(..., min_length=1)
    confirm: bool = Field(...)

    @field_validator('confirm')
    @classmethod
    def confirm_deletion(cls, v: bool):
        if not v:
            raise ValueError('Для удаления задачи необходимо подтверждение (confirm=True)')
        return v

class TaskFilters(BaseModel):
    """Параметры фильтрации и пагинации"""
    status: Optional[TaskStatusEnum] = Field(None, description="Фильтр по статусу")
    priority: Optional[TaskPriorityEnum] = Field(None, description="Фильтр по приоритету")
    skip: int = Field(0, ge=0, description="Сколько задач пропустить")
    limit: int = Field(10, ge=1, le=100, description="Максимум задач на странице")

class PaginationMeta(BaseModel):
    """Метаданные пагинации"""
    total_count: int = Field(..., description="Общее количество задач с учетом фильтров")
    page: int = Field(..., description="Текущая страница (начиная с 1)")
    page_size: int = Field(..., description="Размер страницы")

class TaskListResponse(BaseModel):
    """Ответ со списком задач и пагинацией"""
    data: List[TaskResponse] = Field(..., description="Список задач")
    meta: PaginationMeta = Field(..., description="Метаданные пагинации")

class TaskStatsResponse(BaseModel):
    """Статистика по задачам"""
    pending: int = Field(0, description="Количество ожидающих задач")
    in_progress: int = Field(0, description="Количество задач в работе")
    completed: int = Field(0, description="Количество выполненных задач")
    total: int = Field(0, description="Общее количество задач")