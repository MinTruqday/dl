import functools
import time
from loguru import logger

def log_logic_execution(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(f"Started execution of core logic {func.__name__}")
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Completed execution of core logic {func.__name__} in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"Exception occurred during execution of core logic {func.__name__} after {duration:.3f}s")
            raise e
    return wrapper

def log_logic_execution_sync(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Started execution of core logic {func.__name__}")
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Completed execution of core logic {func.__name__} in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"Exception occurred during execution of core logic {func.__name__} after {duration:.3f}s")
            raise e
    return wrapper
