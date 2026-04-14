from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

# Определяем, что API ключ должен быть в header X-API-Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Проверка API ключа
    
    Ожидает header: X-API-Key: secret-api-key-12345
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Please provide X-API-Key header",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    
    return api_key


# Альтернативная версия с опциональной проверкой (для публичных эндпоинтов)
async def optional_api_key(api_key: str = Security(api_key_header)):
    """
    Опциональная проверка API ключа (не требует обязательной авторизации)
    """
    if api_key and api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return api_key