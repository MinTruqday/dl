import asyncio
from functools import wraps
from loguru import logger
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

def with_retry(max_retries=3, base_wait=2, max_wait=10):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(max_retries),
                    wait=wait_exponential(multiplier=base_wait, max=max_wait),
                    retry=retry_if_exception_type(Exception),
                    reraise=True,
                ):
                    with attempt:
                        return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Operation failed permanently after {max_retries} retry attempts")
                raise e
        return wrapper
    return decorator