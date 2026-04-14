from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import tasks
from app.core.database import db_manager
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.performance_middleware import PerformanceMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_manager.connect()
    print("✅ Application started")
    yield
    # Shutdown
    await db_manager.disconnect()
    print("✅ Application shutdown")


app = FastAPI(
    title="Task Manager API",
    description="API для управления задачами",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Добавляем middleware в правильном порядке
# ВАЖНО: порядок имеет значение - middleware выполняются сверху вниз

# 1. Логирование запросов (первым - логируем всё)
app.add_middleware(LoggingMiddleware)

# 2. Логирование медленных запросов (для производительности)
app.add_middleware(PerformanceMiddleware, slow_threshold=0.5)  # 0.5 секунды порог

# 3. CORS (если нужен доступ с фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Task Manager API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "endpoints": {
            "tasks": "/api/v1/tasks"
        }
    }


# Подключаем роутер для задач
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}