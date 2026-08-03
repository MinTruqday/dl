import asyncio
import json
import traceback
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from langchain_core.exceptions import OutputParserException
from loguru import logger
from src.utils.background import create_background_task
from pydantic import ValidationError

from src.repositories.agent import AgentRepository

FailureType = Literal[
    "BAD_MODEL_CALL",
    "INVALID_TOOL_ARGUMENT",
    "MISSING_CONTEXT",
    "TOOL_TIMEOUT",
    "PERMISSION_DENIED",
    "PLAN_PARSE_ERROR",
    "RETRIEVAL_FAILURE",
    "UNKNOWN",
]

@dataclass
class FailureRecord:
    session_id: str
    user_id: str
    failure_type: FailureType
    node: str
    tool_name: Optional[str]
    error_message: str
    stack_trace: str
    context_snapshot: Dict[str, Any]
    occurred_at: datetime

@dataclass
class AttributionReport:
    session_id: str
    total_failures: int
    failure_breakdown: Dict[str, int] = field(default_factory=dict)
    most_recent: Optional[FailureRecord] = None

def _redact_diagnostics(value: str) -> str:
    from src.core.security.guardrails import guardrails_engine

    result = guardrails_engine.inspect_output(str(value))
    return result.get("sanitized_text", str(value))

def _summarize_context(context_snapshot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not context_snapshot:
        return {}
    summary = {}
    for key, value in list(context_snapshot.items())[:30]:
        normalized = str(key).lower()
        if any(marker in normalized for marker in ("token", "secret", "password", "key", "authorization")):
            summary[str(key)[:80]] = "[REDACTED]"
        elif isinstance(value, (str, bytes, list, tuple, dict, set)):
            summary[str(key)[:80]] = {
                "type": type(value).__name__,
                "size": len(value),
            }
        else:
            summary[str(key)[:80]] = type(value).__name__
    return summary

def _classify_failure(error: Exception, node: str = "") -> FailureType:
    if isinstance(error, (json.JSONDecodeError, OutputParserException)):
        return "BAD_MODEL_CALL"
    if isinstance(error, ValidationError):
        return "INVALID_TOOL_ARGUMENT"
    if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
        return "TOOL_TIMEOUT"
    if isinstance(error, PermissionError):
        return "PERMISSION_DENIED"
    if isinstance(error, KeyError):
        return "MISSING_CONTEXT"
    return "UNKNOWN"

class FailureAttributionHarness:
    def __init__(self):
        self._records: Dict[str, list] = {}

    def record_failure(
        self,
        session_id: str,
        user_id: str,
        error: Exception,
        node: str = "",
        tool_name: Optional[str] = None,
        context_snapshot: Optional[Dict[str, Any]] = None,
    ) -> FailureRecord:
        failure_type = _classify_failure(error, node)
        stack = _redact_diagnostics(traceback.format_exc())
        record = FailureRecord(
            session_id=session_id,
            user_id=user_id,
            failure_type=failure_type,
            node=node,
            tool_name=tool_name,
            error_message=_redact_diagnostics(str(error))[:500],
            stack_trace=stack[:2000],
            context_snapshot=_summarize_context(context_snapshot),
            occurred_at=datetime.now(timezone.utc),
        )
        if session_id not in self._records:
            self._records[session_id] = []
        self._records[session_id].append(record)
        logger.warning(
            f"Session failure recorded: type={failure_type}, node={node or 'unknown'}"
        )
        try:
            asyncio.get_running_loop()
            create_background_task(
                self._persist_record(record),
                f"failure-record-{session_id}-{len(self._records[session_id])}",
            )
        except RuntimeError:
            logger.warning("Failure record persistence skipped without an event loop")
        return record

    async def _persist_record(self, record: FailureRecord):
        try:
            doc = {
                "session_id": record.session_id,
                "user_id": record.user_id,
                "failure_type": record.failure_type,
                "node": record.node,
                "tool_name": record.tool_name,
                "error_message": record.error_message,
                "stack_trace": record.stack_trace,
                "occurred_at": record.occurred_at,
            }
            await AgentRepository.insert_trace(doc)
            logger.info("Session failure record persisted to MongoDB")
        except Exception:
            logger.exception("Error persisting session failure record to MongoDB")

    def get_report(self, session_id: str) -> AttributionReport:
        records = self._records.get(session_id, [])
        breakdown: Dict[str, int] = {}
        for record in records:
            breakdown[record.failure_type] = breakdown.get(record.failure_type, 0) + 1
        return AttributionReport(
            session_id=session_id,
            total_failures=len(records),
            failure_breakdown=breakdown,
            most_recent=records[-1] if records else None,
        )

    def clear_session(self, session_id: str):
        self._records.pop(session_id, None)

    def classify(self, error: Exception, node: str = "") -> FailureType:
        return _classify_failure(error, node)

failure = FailureAttributionHarness()
