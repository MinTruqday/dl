from datetime import datetime, timezone
from typing import Any


ALLOWED_TECHNICAL_FLAGS = {
    "browser_reload",
    "network_error",
    "offline_retry",
    "visibility_hidden",
}


def derive_assigned_telemetry(payload: dict[str, Any], started_at: datetime, captured_at: datetime):
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    elapsed_ms = max(0, int((captured_at - started_at).total_seconds() * 1000))
    reported_ms = max(0, int(payload.get("response_time_ms", 0)))
    technical_flags = {
        value
        for value in payload.get("technical_flags", [])
        if isinstance(value, str) and value in ALLOWED_TECHNICAL_FLAGS
    }
    if reported_ms > elapsed_ms + 5000:
        technical_flags.add("abnormal_time")
    return {
        "response_time_ms": min(reported_ms, elapsed_ms),
        "technical_flags": sorted(technical_flags),
    }
