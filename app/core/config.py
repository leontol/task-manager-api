from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Task Manager API"
    version: str = "1.0.0"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    
    # API Key
    api_key: str = "secret-api-key-12345"
    
    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "admin"
    db_password: str = "admin123"
    db_name: str = "taskdb"
    db_pool_min_size: int = 1
    db_pool_max_size: int = 10
    
    # Использовать БД или in-memory
    use_database: bool = True  # ← Включаем PostgreSQL
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()