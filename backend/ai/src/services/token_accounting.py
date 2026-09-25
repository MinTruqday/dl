from contextvars import ContextVar
from typing import Any

_usage: ContextVar[dict[str, int] | None] = ContextVar("model_usage", default=None)


def start_accounting() -> None:
    _usage.set({"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "tool_tokens": 0})


def usage_values(response: Any, input_chars: int, output_chars: int) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if isinstance(usage, dict):
        get_value = usage.get
    else:
        def get_value(key, default=0):
            return getattr(usage, key, default)
    prompt = int(get_value("prompt_tokens", 0) or get_value("input_tokens", 0) or 0)
    completion = int(get_value("completion_tokens", 0) or get_value("output_tokens", 0) or 0)
    cached = int(get_value("cached_tokens", 0) or get_value("cache_read_input_tokens", 0) or 0)
    return {
        "input_tokens": prompt or max(1, input_chars // 4),
        "output_tokens": completion or max(1, output_chars // 4),
        "cached_tokens": cached,
    }


def record_usage(response: Any, input_chars: int, output_chars: int) -> dict[str, int]:
    values = usage_values(response, input_chars, output_chars)
    current = _usage.get()
    if current is not None:
        for key, value in values.items():
            current[key] += value
    return values


def add_tool_usage(tokens: int) -> None:
    current = _usage.get()
    if current is not None:
        current["tool_tokens"] += max(0, int(tokens))


def current_usage() -> dict[str, int]:
    return dict(
        _usage.get()
        or {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "tool_tokens": 0}
    )
