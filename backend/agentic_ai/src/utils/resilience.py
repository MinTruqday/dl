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
                        logger.error("The underlying sequential algorithm significantly violated absolute maximum timing variables definitively terminating")
                        raise e
                    logger.warning("The operational dynamic networking logic encountered turbulence invoking automated systematic execution retry parameters")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator