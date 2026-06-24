import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from loguru import logger

from shared.repositories.base_repository import RepositoryFactory


@dataclass
class TraceEvent:
    event_type: str
    session_id: str
    user_id: str
    timestamp: datetime
    data: dict = field(default_factory=dict)


@dataclass
class SessionMetrics:
    session_id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: Literal["running", "done", "failed", "cancelled"] = "running"
    total_tool_calls: int = 0
    total_llm_calls: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_duration_ms: int = 0
    security_violations: int = 0
    tool_call_breakdown: dict = field(default_factory=dict)
    llm_latencies_ms: list = field(default_factory=list)


PROMETHEUS_PREFIX = "system_agent"


class AgentopsHarness:
    def __init__(self):
        self._sessions: dict[str, SessionMetrics] = {}
        self._db_client = None
        self._lock = asyncio.Lock()
        self._pending_flush: list[dict] = []
        self._flush_task: Optional[asyncio.Task] = None

    def _get_db(self):
        if self._db_client is None:
            try:
                from motor.motor_asyncio import AsyncIOMotorClient

                from shared.infrastructure.configuration import settings

                client = AsyncIOMotorClient(settings.MONGODB_URI)
                self._db_client = client.get_default_database()
            except Exception as e:
                logger.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
        return self._db_client

    def record_session_start(
        self, session_id: str, user_id: str, query_preview: str = ""
    ):
        metrics = SessionMetrics(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.now(timezone.utc),
        )
        self._sessions[session_id] = metrics
        logger.info("Bắt đầu ghi lại phiên làm việc thành công")

    def record_session_end(
        self,
        session_id: str,
        status: Literal["done", "failed", "cancelled"] = "done",
    ):
        metrics = self._sessions.get(session_id)
        if not metrics:
            return
        metrics.ended_at = datetime.now(timezone.utc)
        metrics.status = status
        metrics.total_duration_ms = int(
            (metrics.ended_at - metrics.started_at).total_seconds() * 1000
        )
        logger.info("Kết thúc quá trình ghi lại phiên làm việc")
        asyncio.create_task(self._flush_session(session_id))

    def record_tool_call(
        self,
        session_id: str,
        tool_name: str,
        duration_ms: int,
        success: bool,
        error: str = "",
    ):
        metrics = self._sessions.get(session_id)
        if metrics:
            metrics.total_tool_calls += 1
            breakdown = metrics.tool_call_breakdown.setdefault(
                tool_name, {"count": 0, "errors": 0, "total_ms": 0}
            )
            breakdown["count"] += 1
            breakdown["total_ms"] += duration_ms
            if not success:
                breakdown["errors"] += 1
        log_fn = logger.info if success else logger.warning
        log_fn(
            "The system successfully recorded the execution event for the invoked utility"
        )

    def record_llm_call(
        self,
        session_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: int,
    ):
        metrics = self._sessions.get(session_id)
        if metrics:
            metrics.total_llm_calls += 1
            metrics.total_tokens_in += prompt_tokens
            metrics.total_tokens_out += completion_tokens
            metrics.llm_latencies_ms.append(duration_ms)
        logger.info("Ghi nhận sự kiện gọi mô hình ngôn ngữ thành công")

    def record_security_event(
        self,
        session_id: str,
        event_type: str,
        risk_score: float,
        violations: list = None,
    ):
        metrics = self._sessions.get(session_id)
        if metrics:
            metrics.security_violations += 1
        logger.warning("Ghi nhận rủi ro vi phạm bảo mật")

    async def _flush_session(self, session_id: str):
        metrics = self._sessions.pop(session_id, None)
        if not metrics:
            return
        db = self._get_db()
        if not db:
            return
        try:
            doc = {
                "session_id": metrics.session_id,
                "user_id": metrics.user_id,
                "status": metrics.status,
                "started_at": metrics.started_at,
                "ended_at": metrics.ended_at,
                "total_duration_ms": metrics.total_duration_ms,
                "total_tool_calls": metrics.total_tool_calls,
                "total_llm_calls": metrics.total_llm_calls,
                "total_tokens_in": metrics.total_tokens_in,
                "total_tokens_out": metrics.total_tokens_out,
                "security_violations": metrics.security_violations,
                "tool_call_breakdown": metrics.tool_call_breakdown,
                "avg_llm_latency_ms": (
                    int(sum(metrics.llm_latencies_ms) / len(metrics.llm_latencies_ms))
                    if metrics.llm_latencies_ms
                    else 0
                ),
            }
            await RepositoryFactory.get("agent_traces").insert_one(doc)
            logger.info("Lưu lịch sử phiên làm việc thành công")
        except Exception as e:
            logger.error(f"Lỗi lưu lịch sử phiên làm việc: {e}")

    def get_prometheus_metrics(self) -> str:
        active_count = len(self._sessions)
        running_sessions = [m for m in self._sessions.values() if m.status == "running"]

        total_tool_calls = sum(m.total_tool_calls for m in running_sessions)
        total_llm_calls = sum(m.total_llm_calls for m in running_sessions)
        total_tokens = sum(
            m.total_tokens_in + m.total_tokens_out for m in running_sessions
        )
        security_events = sum(m.security_violations for m in running_sessions)

        lines = [
            f"# HELP {PROMETHEUS_PREFIX}_active_sessions Number of active agent session",
            f"# TYPE {PROMETHEUS_PREFIX}_active_sessions gauge",
            f"{PROMETHEUS_PREFIX}_active_sessions {active_count}",
            f"# HELP {PROMETHEUS_PREFIX}_tool_calls_total Tool calls in active session",
            f"# TYPE {PROMETHEUS_PREFIX}_tool_calls_total counter",
            f"{PROMETHEUS_PREFIX}_tool_calls_total {total_tool_calls}",
            f"# HELP {PROMETHEUS_PREFIX}_llm_calls_total LLM calls in active session",
            f"# TYPE {PROMETHEUS_PREFIX}_llm_calls_total counter",
            f"{PROMETHEUS_PREFIX}_llm_calls_total {total_llm_calls}",
            f"# HELP {PROMETHEUS_PREFIX}_tokens_total Total tokens (in+out) in active session",
            f"# TYPE {PROMETHEUS_PREFIX}_tokens_total counter",
            f"{PROMETHEUS_PREFIX}_tokens_total {total_tokens}",
            f"# HELP {PROMETHEUS_PREFIX}_security_violations_total Security violations in active session",
            f"# TYPE {PROMETHEUS_PREFIX}_security_violations_total counter",
            f"{PROMETHEUS_PREFIX}_security_violations_total {security_events}",
        ]

        for session in running_sessions:
            for tool_name, breakdown in session.tool_call_breakdown.items():
                avg_ms = breakdown["total_ms"] // max(breakdown["count"], 1)
                safe_tool = tool_name.lower().replace(" ", "_")
                lines.append(
                    f'{PROMETHEUS_PREFIX}_tool_avg_latency_ms{{tool="{safe_tool}"}} {avg_ms}'
                )

        return "\n".join(lines) + "\n"


agentops = AgentopsHarness()
