import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api")

class RequestBodyLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования тела запроса (только для POST/PUT)"""
    
    async def dispatch(self, request: Request, call_next):
        # Сохраняем тело запроса только для методов, которые его имеют
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Читаем тело запроса
                body = await request.body()
                body_str = body.decode("utf-8") if body else ""
                
                # Пытаемся отформатировать JSON
                if body_str:
                    try:
                        body_json = json.loads(body_str)
                        # Скрываем API ключ, если он есть в теле
                        if "api_key" in body_json:
                            body_json["api_key"] = "***HIDDEN***"
                        logger.info(f"[BODY] {json.dumps(body_json, ensure_ascii=False)}")
                    except:
                        logger.info(f"[BODY] {body_str[:200]}")  # Ограничиваем длину
                
                # Восстанавливаем тело для дальнейшей обработки
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
                
            except Exception as e:
                logger.warning(f"Could not log request body: {e}")
        
        response = await call_next(request)
        return response