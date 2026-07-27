import json
import time
from typing import Any, Callable

from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from loguru import logger


SENSITIVE_FIELD_MARKERS = frozenset(
    {
        "authorization",
        "cookie",
        "credential",
        "key",
        "password",
        "secret",
        "token",
    }
)


def _safe_field_name(name: Any) -> str:
    normalized = str(name).strip().lower()
    if any(marker in normalized for marker in SENSITIVE_FIELD_MARKERS):
        return "[sensitive]"
    return normalized[:80]


def summarize_payload(body: bytes) -> dict[str, Any]:
    summary: dict[str, Any] = {"body_bytes": len(body)}
    if not body:
        summary["body_type"] = "empty"
        return summary
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        summary["body_type"] = "non_json"
        return summary
    if isinstance(payload, dict):
        summary["body_type"] = "object"
        summary["body_fields"] = sorted(
            {_safe_field_name(key) for key in payload.keys()}
        )[:30]
    elif isinstance(payload, list):
        summary["body_type"] = "array"
        summary["body_items"] = len(payload)
    else:
        summary["body_type"] = type(payload).__name__
    return summary


class LoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            body_summary = summarize_payload(await request.body())
            query_fields = sorted(
                {_safe_field_name(key) for key in request.query_params.keys()}
            )[:30]
            logger.info(
                "API request started method={} path={} query_fields={} body_summary={}",
                request.method,
                request.url.path,
                query_fields,
                body_summary,
            )
            started_at = time.monotonic()
            try:
                response: Response = await original_route_handler(request)
            except HTTPException as exc:
                duration_ms = int((time.monotonic() - started_at) * 1000)
                logger.warning(
                    "API request rejected method={} path={} status={} duration_ms={}",
                    request.method,
                    request.url.path,
                    exc.status_code,
                    duration_ms,
                )
                raise
            except RequestValidationError as exc:
                duration_ms = int((time.monotonic() - started_at) * 1000)
                logger.warning(
                    "API request validation failed method={} path={} issues={} duration_ms={}",
                    request.method,
                    request.url.path,
                    len(exc.errors()),
                    duration_ms,
                )
                raise
            except Exception:
                duration_ms = int((time.monotonic() - started_at) * 1000)
                logger.exception(
                    "API request failed method={} path={} duration_ms={}",
                    request.method,
                    request.url.path,
                    duration_ms,
                )
                raise
            duration_ms = int((time.monotonic() - started_at) * 1000)
            logger.info(
                "API request completed method={} path={} status={} duration_ms={}",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
            return response

        return custom_route_handler
