import asyncio
import time
from typing import Any, Sequence

from loguru import logger


class ModelInvocationError(RuntimeError):
    pass


def _content_size(messages: Sequence[dict[str, Any]]) -> int:
    total = 0
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    total += len(item["text"])
    return total


async def run_chat_completion(
    client: Any,
    messages: Sequence[dict[str, Any]],
    model: str,
    max_tokens: int,
    temperature: float,
    attempts: int = 3,
    timeout_seconds: float = 60.0,
) -> str:
    if attempts < 1:
        raise ValueError("Model invocation attempts must be positive")
    if timeout_seconds <= 0:
        raise ValueError("Model invocation timeout must be positive")
    if max_tokens < 1:
        raise ValueError("Model output token limit must be positive")
    input_chars = _content_size(messages)
    started_at = time.monotonic()
    logger.info(
        "Model invocation started model={} messages={} input_chars={} max_tokens={}",
        model,
        len(messages),
        input_chars,
        max_tokens,
    )
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        attempt_started_at = time.monotonic()
        try:
            async with asyncio.timeout(timeout_seconds):
                response = await client.chat_completion(
                    model=model,
                    messages=list(messages),
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            choices = getattr(response, "choices", None)
            if not choices:
                raise ModelInvocationError("Model returned no completion choices")
            content = getattr(choices[0].message, "content", None)
            if not isinstance(content, str) or not content.strip():
                raise ModelInvocationError("Model returned empty text content")
            logger.info(
                "Model invocation completed model={} attempt={} output_chars={} duration_ms={}",
                model,
                attempt,
                len(content),
                int((time.monotonic() - started_at) * 1000),
            )
            return content
        except asyncio.CancelledError:
            logger.warning(
                "Model invocation cancelled model={} attempt={} duration_ms={}",
                model,
                attempt,
                int((time.monotonic() - attempt_started_at) * 1000),
            )
            raise
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                delay_seconds = min(2 ** (attempt - 1), 4)
                logger.warning(
                    "Model invocation retry model={} attempt={} next_attempt={} delay_seconds={} error_type={}",
                    model,
                    attempt,
                    attempt + 1,
                    delay_seconds,
                    type(exc).__name__,
                )
                await asyncio.sleep(delay_seconds)
                continue
            logger.exception(
                "Model invocation failed model={} attempts={} duration_ms={}",
                model,
                attempts,
                int((time.monotonic() - started_at) * 1000),
            )
    raise ModelInvocationError("Model invocation failed") from last_error
