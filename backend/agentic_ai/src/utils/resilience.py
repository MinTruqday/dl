import asyncio
from functools import wraps
from loguru import logger

def async_retry(retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries:
                        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
                        raise e
                    logger.warning("Mất kết nối mạng tạm thời")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator