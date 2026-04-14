import time
import logging
import sys
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Настройка логгера с поддержкой UTF-8 для Windows
if sys.platform == "win32":
    # Настраиваем консоль для поддержки UTF-8
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/api.log", encoding='utf-8'),  # UTF-8 для файла
        logging.StreamHandler(sys.stdout)  # Используем stdout
    ]
)

logger = logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования всех HTTP запросов"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Собираем информацию о запросе
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # Логируем запрос (без эмодзи)
        logger.info(f"[REQUEST] {method} {url} - Client: {client_host}")
        
        # Обрабатываем запрос
        try:
            response = await call_next(request)
            
            # Вычисляем время выполнения
            process_time = time.time() - start_time
            
            # Логируем ответ (без эмодзи)
            logger.info(
                f"[RESPONSE] {method} {url} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            # Добавляем заголовок с временем выполнения
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Логируем ошибку (без эмодзи)
            logger.error(f"[ERROR] {method} {url} - {str(e)}")
            raise