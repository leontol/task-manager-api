import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api")

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware для обнаружения медленных запросов"""
    
    def __init__(self, app, slow_threshold: float = 1.0):
        super().__init__(app)
        self.slow_threshold = slow_threshold
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Логируем медленные запросы (без эмодзи)
        if process_time > self.slow_threshold:
            logger.warning(
                f"[SLOW REQUEST] {request.method} {request.url.path} - "
                f"Time: {process_time:.3f}s (threshold: {self.slow_threshold}s)"
            )
        
        return response