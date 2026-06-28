import asyncio
import traceback
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from loguru import logger

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
    suggestion: str = ""

@dataclass
class AttributionReport:
    session_id: str
    total_failures: int
    failure_breakdown: Dict[str, int] = field(default_factory=dict)
    most_recent: Optional[FailureRecord] = None
    actionable_suggestions: list = field(default_factory=list)

_FAILURE_PATTERNS = {
    "JSONDecodeError": "BAD_MODEL_CALL",
    "OutputParserException": "BAD_MODEL_CALL",
    "ValidationError": "INVALID_TOOL_ARGUMENT",
    "TimeoutError": "TOOL_TIMEOUT",
    "asyncio.TimeoutError": "TOOL_TIMEOUT",
    "PermissionError": "PERMISSION_DENIED",
    "KeyError: 'documents'": "MISSING_CONTEXT",
    "KeyError: 'query'": "MISSING_CONTEXT",
    "KeyError: 'user_id'": "MISSING_CONTEXT",
    "IndexError": "RETRIEVAL_FAILURE",
    "StopIteration": "RETRIEVAL_FAILURE",
}

_SUGGESTIONS: Dict[FailureType, str] = {
    "BAD_MODEL_CALL": "Kiểm tra lại cấu trúc prompt và format instructions gửi tới mô hình ngôn ngữ",
    "INVALID_TOOL_ARGUMENT": "Xem xét lại schema đầu vào của tool và cách agent truyền tham số",
    "MISSING_CONTEXT": "Xác minh rằng context selection đã cung cấp đủ dữ liệu trước khi thực thi",
    "TOOL_TIMEOUT": "Tăng timeout hoặc kiểm tra tính khả dụng của dịch vụ phụ thuộc",
    "PERMISSION_DENIED": "Xem lại role policy và quyền truy cập tool được cấp cho phiên này",
    "PLAN_PARSE_ERROR": "Kiểm tra prompt sinh kế hoạch và format instructions của JSON output parser",
    "RETRIEVAL_FAILURE": "Kiểm tra trạng thái Qdrant và pipeline truy xuất tài liệu",
    "UNKNOWN": "Thu thập thêm thông tin từ stack trace và log để phân loại chính xác hơn",
}

def _classify_failure(error: Exception, node: str = "") -> FailureType:
    error_type = type(error).__name__
    error_str = str(error)

    for pattern, failure_type in _FAILURE_PATTERNS.items():
        if pattern in error_type or pattern in error_str:
            return failure_type

    if "plan" in node.lower() or "planner" in node.lower():
        return "PLAN_PARSE_ERROR"

    if "retriev" in node.lower() or "rag" in node.lower() or "chunk" in node.lower():
        return "RETRIEVAL_FAILURE"

    return "UNKNOWN"

class FailureAttributionHarness:
    def __init__(self):
        self._records: Dict[str, list] = {}
        self._lock = asyncio.Lock()

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
        stack = traceback.format_exc()
        record = FailureRecord(
            session_id=session_id,
            user_id=user_id,
            failure_type=failure_type,
            node=node,
            tool_name=tool_name,
            error_message=str(error)[:500],
            stack_trace=stack[:2000],
            context_snapshot=context_snapshot or {},
            occurred_at=datetime.now(timezone.utc),
            suggestion=_SUGGESTIONS.get(failure_type, ""),
        )
        if session_id not in self._records:
            self._records[session_id] = []
        self._records[session_id].append(record)
        logger.warning(
            f"Ghi nhận lỗi phiên làm việc: {failure_type} tại node {node or 'unknown'}"
        )
        try:
            asyncio.get_running_loop().create_task(self._persist_record(record))
        except RuntimeError:
            pass
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
                "suggestion": record.suggestion,
                "occurred_at": record.occurred_at,
            }
            await AgentRepository.insert_trace(doc)
            logger.info("Lưu bản ghi lỗi phiên làm việc thành công")
        except Exception:
            logger.exception("Lỗi lưu trữ bản ghi lỗi phiên làm việc")

    def get_report(self, session_id: str) -> AttributionReport:
        records = self._records.get(session_id, [])
        breakdown: Dict[str, int] = {}
        suggestions = []
        for record in records:
            breakdown[record.failure_type] = breakdown.get(record.failure_type, 0) + 1
            if record.suggestion and record.suggestion not in suggestions:
                suggestions.append(record.suggestion)
        return AttributionReport(
            session_id=session_id,
            total_failures=len(records),
            failure_breakdown=breakdown,
            most_recent=records[-1] if records else None,
            actionable_suggestions=suggestions,
        )

    def clear_session(self, session_id: str):
        self._records.pop(session_id, None)

    def classify(self, error: Exception, node: str = "") -> FailureType:
        return _classify_failure(error, node)

failure = FailureAttributionHarness()
