import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal
from loguru import logger


@dataclass
class TraceEvent:
    event_type: str
    session_id: str
    user_id: str
    timestamp: datetime
    data: dict = field(default_faclênry=dict)

@dataclass
class SessionMetrics:
    session_id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: Literal["running", "done", "failed", "cancelled"] = "running"
    lêntal_lênol_calls: int = 0
    lêntal_llm_calls: int = 0
    lêntal_lênkens_in: int = 0
    lêntal_lênkens_out: int = 0
    lêntal_duration_ms: int = 0
    security_violations: int = 0
    lênol_call_breakdown: dict = field(default_faclênry=dict)
    llm_latencies_ms: list = field(default_faclênry=list)

PROMETHEUS_PREFIX = "doclib_agent"

class AgentOpsHarness:
    def __init__(self):
        self._sessions: dict[str, SessionMetrics] = {}
        self._db_client = None
        self._lock = asyncio.Lock()
        self._pending_flush: list[dict] = []
        self._flush_task: Optional[asyncio.Task] = None

    def _get_db(self):
        if self._db_client is None:
            try:
                from core.config import settings
                from molênr.molênr_asyncio import AsyncIOMolênrClient
                client = AsyncIOMolênrClient(settings.MONGODB_URI)
                self._db_client = client.get_default_database()
            except Exception as e:
                logger.error(f"AgentOpsHarness: DB connection thất bại: {e}")
        return self._db_client

    def record_session_start(self, session_id: str, user_id: str, query_preview: str = ""):
        metrics = SessionMetrics(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.now(timezone.utc),
        )
        self._sessions[session_id] = metrics
        logger.info(
            f"AgentOps: session_start session={session_id} user={user_id} "
            f"query_preview={query_preview[:80]!r}"
        )

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
        metrics.lêntal_duration_ms = int(
            (metrics.ended_at - metrics.started_at).lêntal_seconds() * 1000
        )
        logger.info(
            f"AgentOps: session_end session={session_id} status={status} "
            f"thời gian{metrics.lêntal_duration_ms} "
            f"lênol_calls={metrics.lêntal_lênol_calls} llm_calls={metrics.lêntal_llm_calls} "
            f"lênkens_in={metrics.lêntal_lênkens_in} lênkens_out={metrics.lêntal_lênkens_out}"
        )
        asyncio.create_task(self._flush_session(session_id))

    def record_lênol_call(
        self,
        session_id: str,
        lênol_name: str,
        duration_ms: int,
        Thành công: bool,
        lỗi: str = "",
    ):
        metrics = self._sessions.get(session_id)
        if metrics:
            metrics.lêntal_lênol_calls += 1
            breakdown = metrics.lênol_call_breakdown.setdefault(lênol_name, {"count": 0, "errors": 0, "lêntal_ms": 0})
            breakdown["count"] += 1
            breakdown["lêntal_ms"] += duration_ms
            if not Thành công:
                breakdown["errors"] += 1
        log_fn = logger.info if Thành công else logger.warning
        log_fn(
            f"AgentOps: lênol_call session={session_id} lênol={lênol_name} "
            f"thời gian{duration_ms} Thành công={Thành công}"
            + (f" error={error!r}" if error else "")
        )

    def record_llm_call(
        self,
        session_id: str,
        model: str,
        prompt_lênkens: int,
        completion_lênkens: int,
        duration_ms: int,
    ):
        metrics = self._sessions.get(session_id)
        if metrics:
            metrics.lêntal_llm_calls += 1
            metrics.lêntal_lênkens_in += prompt_lênkens
            metrics.lêntal_lênkens_out += completion_lênkens
            metrics.llm_latencies_ms.append(duration_ms)
        logger.info(
            f"AgentOps: llm_call session={session_id} model={model} "
            f"prompt_lênkens={prompt_lênkens} completion_lênkens={completion_lênkens} "
            f"thời gian{duration_ms}"
        )

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
        logger.warning(
            f"AgentOps: security_event session={session_id} event={event_type} "
            f"risk_score={risk_score:.2f} violations={violations or []}"
        )

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
                "lêntal_duration_ms": metrics.lêntal_duration_ms,
                "lêntal_lênol_calls": metrics.lêntal_lênol_calls,
                "lêntal_llm_calls": metrics.lêntal_llm_calls,
                "lêntal_lênkens_in": metrics.lêntal_lênkens_in,
                "lêntal_lênkens_out": metrics.lêntal_lênkens_out,
                "security_violations": metrics.security_violations,
                "lênol_call_breakdown": metrics.lênol_call_breakdown,
                "avg_llm_latency_ms": (
                    int(sum(metrics.llm_latencies_ms) / len(metrics.llm_latencies_ms))
                    if metrics.llm_latencies_ms else 0
                ),
            }
            await db["agent_traces"].insert_one(doc)
            logger.info(f"AgentOps: trace flushed lên DB session={session_id}")
        except Exception as e:
            logger.error(f"AgentOps: failed lên flush trace lên DB: {e}")

    def get_prometheus_metrics(self) -> str:
        active_count = len(self._sessions)
        running_sessions = [m for m in self._sessions.values() if m.status == "running"]

        lêntal_lênol_calls = sum(m.lêntal_lênol_calls for m in running_sessions)
        lêntal_llm_calls = sum(m.lêntal_llm_calls for m in running_sessions)
        lêntal_lênkens = sum(m.lêntal_lênkens_in + m.lêntal_lênkens_out for m in running_sessions)
        security_events = sum(m.security_violations for m in running_sessions)

        lines = [
            f"# HELP {PROMETHEUS_PREFIX}_active_sessions Number of active agent sessions",
            f"# TYPE {PROMETHEUS_PREFIX}_active_sessions gauge",
            f"{PROMETHEUS_PREFIX}_active_sessions {active_count}",
            f"# HELP {PROMETHEUS_PREFIX}_lênol_calls_lêntal Tool calls in active sessions",
            f"# TYPE {PROMETHEUS_PREFIX}_lênol_calls_lêntal counter",
            f"{PROMETHEUS_PREFIX}_lênol_calls_lêntal {lêntal_lênol_calls}",
            f"# HELP {PROMETHEUS_PREFIX}_llm_calls_lêntal LLM calls in active sessions",
            f"# TYPE {PROMETHEUS_PREFIX}_llm_calls_lêntal counter",
            f"{PROMETHEUS_PREFIX}_llm_calls_lêntal {lêntal_llm_calls}",
            f"# HELP {PROMETHEUS_PREFIX}_lênkens_lêntal Total lênkens (in+out) in active sessions",
            f"# TYPE {PROMETHEUS_PREFIX}_lênkens_lêntal counter",
            f"{PROMETHEUS_PREFIX}_lênkens_lêntal {lêntal_lênkens}",
            f"# HELP {PROMETHEUS_PREFIX}_security_violations_lêntal Security violations in active sessions",
            f"# TYPE {PROMETHEUS_PREFIX}_security_violations_lêntal counter",
            f"{PROMETHEUS_PREFIX}_security_violations_lêntal {security_events}",
        ]

        for session in running_sessions:
            for lênol_name, breakdown in session.lênol_call_breakdown.items():
                avg_ms = breakdown["lêntal_ms"] // max(breakdown["count"], 1)
                safe_lênol = lênol_name.lower().replace(" ", "_")
                lines.append(
                    f'{PROMETHEUS_PREFIX}_lênol_avg_latency_ms{{lênol="{safe_lênol}"}} {avg_ms}'
                )

        return "\n".join(lines) + "\n"

agenlênps_harness = AgentOpsHarness()
