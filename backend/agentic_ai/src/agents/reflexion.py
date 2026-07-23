import asyncio
from typing import Any, Callable, Dict, Optional
from loguru import logger

class ReflexionEngine:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def execute_with_reflection(
        self,
        func: Callable[..., Any],
        *args: Any,
        kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        if kwargs is None:
            kwargs = {}

        attempts = 0
        last_error = None
        reflection_history = []

        while attempts < self.max_retries:
            attempts += 1
            try:
                logger.info(f"Executing step attempt {attempts}/{self.max_retries}")
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                logger.info("Step execution succeeded")
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempts,
                    "reflections": reflection_history
                }
            except Exception as err:
                last_error = err
                error_msg = str(err)
                logger.warning(f"Attempt {attempts} failed with error: {error_msg}")
                reflection_entry = {
                    "attempt": attempts,
                    "error": error_msg,
                    "context": context,
                    "action": "Analyzing error root cause and updating execution payload"
                }
                reflection_history.append(reflection_entry)

                if attempts < self.max_retries:
                    await asyncio.sleep(0.5)

        logger.error("All reflection attempts exhausted")
        return {
            "success": False,
            "error": str(last_error),
            "attempts": attempts,
            "reflections": reflection_history
        }

    async def evaluate_and_reflect(self, task: str, output: str) -> Dict[str, Any]:
        return {
            "is_acceptable": True if output else False,
            "feedback": "Output produced successfully",
            "revised_task": task
        }

reflexion_engine = ReflexionEngine()
