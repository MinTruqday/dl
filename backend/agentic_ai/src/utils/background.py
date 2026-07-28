import asyncio
from collections.abc import Awaitable
from typing import Any

from loguru import logger

_background_tasks: set[asyncio.Task[Any]] = set()

def create_background_task(
    awaitable: Awaitable[Any],
    name: str,
) -> asyncio.Task[Any]:
    task = asyncio.create_task(awaitable, name=name)
    _background_tasks.add(task)

    def finalize(completed: asyncio.Task[Any]) -> None:
        _background_tasks.discard(completed)
        if completed.cancelled():
            return
        error = completed.exception()
        if error is not None:
            logger.opt(exception=error).error(
                "Background task failed name={}",
                completed.get_name(),
            )

    task.add_done_callback(finalize)
    return task

async def drain_background_tasks(timeout_seconds: float = 10.0) -> None:
    pending = [task for task in _background_tasks if not task.done()]
    if not pending:
        return
    done, remaining = await asyncio.wait(pending, timeout=timeout_seconds)
    for task in done:
        if not task.cancelled():
            task.exception()
    for task in remaining:
        task.cancel()
