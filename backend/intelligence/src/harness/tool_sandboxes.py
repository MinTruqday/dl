import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

from loguru import logger

from shared.infrastructure.config import settings

DEFAULT_TOOL_TIMEOUT_SECONDS = settings.TOOL_TIMEOUT_SECONDS
DEFAULT_MAX_RETRIES = settings.TOOL_MAX_RETRIES
RETRY_BASE_DELAY_SECONDS = 0.5


@dataclass
class ToolResult:
    success: bool
    data: Any
    error: str = ""
    duration_ms: int = 0
    attempt: int = 1


@dataclass
class ToolDefinition:
    name: str
    callable: Callable
    timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    is_async: bool = True


class ToolHarness:
    def __init__(self):
        self._registry: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        callable_fn: Callable,
        timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        is_async: bool = True,
    ):
        self._registry[name] = ToolDefinition(
            name=name,
            callable=callable_fn,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            is_async=is_async,
        )
        logger.info("Tiện ích AI đã được đăng ký")

    def is_registered(self, name: str) -> bool:
        return name in self._registry

    async def execute(
        self,
        tool_name: str,
        session_id: str = "",
        *args,
        **kwargs,
    ) -> ToolResult:
        definition = self._registry.get(tool_name)
        if not definition:
            logger.error("Tiện ích AI chưa được đăng ký")
            return ToolResult(
                success=False,
                data=None,
                error="The requested utility is currently not registered or unavailable in the system",
            )

        start_ms = time.monotonic()
        last_error = ""
        attempt = 0

        for attempt in range(1, definition.max_retries + 2):
            try:
                if definition.is_async:
                    coro = definition.callable(*args, **kwargs)
                    result_data = await asyncio.wait_for(
                        coro, timeout=definition.timeout_seconds
                    )
                else:
                    result_data = await asyncio.wait_for(
                        asyncio.to_thread(definition.callable, *args, **kwargs),
                        timeout=definition.timeout_seconds,
                    )

                duration_ms = int((time.monotonic() - start_ms) * 1000)
                logger.info("Thực thi tác vụ AI thành công")
                return ToolResult(
                    success=True,
                    data=result_data,
                    duration_ms=duration_ms,
                    attempt=attempt,
                )

            except asyncio.TimeoutError:
                last_error = "The execution of the utility exceeded the maximum allowed processing time and was forcefully terminated"
                logger.warning("Trí tuệ nhân tạo không phản hồi")

            except Exception:
                last_error = "The utility encountered an unexpected internal exception during its execution phase"
                logger.warning("Lỗi thực thi tác vụ AI")

            if attempt <= definition.max_retries:
                delay = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        duration_ms = int((time.monotonic() - start_ms) * 1000)
        logger.error("Tiện ích AI không thể thực thi")
        return ToolResult(
            success=False,
            data=None,
            error=last_error,
            duration_ms=duration_ms,
            attempt=attempt,
        )

    def list_tools(self) -> list[str]:
        return list(self._registry.keys())


tool = ToolHarness()
