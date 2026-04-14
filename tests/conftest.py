import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db_manager
from app.repositories.task_repository import TaskRepository


@pytest.fixture(scope="session")
def client():
    """HTTP клиент для тестирования API"""
    db_manager.use_db = False
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_database():
    """Очищает базу данных перед каждым тестом"""
    TaskRepository.clear()
    yield
    TaskRepository.clear()


@pytest.fixture
def api_key_headers():
    """Заголовки с API ключом"""
    return {"X-API-Key": "secret-api-key-12345"}