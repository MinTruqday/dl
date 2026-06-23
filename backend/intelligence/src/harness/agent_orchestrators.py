import asyncio
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Optional

from loguru import logger

SESSION_HARD_TIMEOUT_SECONDS = 120
from shared.infrastructure.config import settings

CIRCUIT_BREAKER_FAILURE_THRESHOLD = settings.CIRCUIT_BREAKER_THRESHOLD
CIRCUIT_BREAKER_RESET_SECONDS = settings.CIRCUIT_BREAKER_RESET_SECONDS


@dataclass
class SessionState:
    session_id: str
    status: Literal["running", "done", "failed", "cancelled", "timeout"] = "running"
    started_at: float = 0.0


class FaultTolerance:
    def __init__(self, threshold: int, reset_seconds: float):
        self._failures = 0
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._tripped_at: Optional[float] = None

    def record_failure(self):
        self._failures += 1
        if self._failures >= self._threshold and not self._tripped_at:
            self._tripped_at = time.monotonic()
            logger.error("Paused due to continuous errors")

    def record_success(self):
        self._failures = 0
        self._tripped_at = None

    def is_open(self) -> bool:
        if not self._tripped_at:
            return False
        elapsed = time.monotonic() - self._tripped_at
        if elapsed >= self._reset_seconds:
            logger.info("Recovering operation")
            self._tripped_at = None
            self._failures = 0
            return False
        return True

    def remaining_seconds(self) -> float:
        if not self._tripped_at:
            return 0.0
        return max(0.0, self._reset_seconds - (time.monotonic() - self._tripped_at))


class OrchestrationHarness:
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
        self._circuit_breaker = FaultTolerance(
            threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            reset_seconds=CIRCUIT_BREAKER_RESET_SECONDS,
        )

    def _open_session(self, session_id: str):
        self._sessions[session_id] = SessionState(
            session_id=session_id,
            status="running",
            started_at=time.monotonic(),
        )

    def _close_session(
        self, session_id: str, status: Literal["done", "failed", "cancelled", "timeout"]
    ):
        state = self._sessions.pop(session_id, None)
        if state:
            state.status = status

    async def run(
        self,
        supervisor_execute_plan,
        req,
        session_id: str,
    ) -> AsyncGenerator[dict, None]:
        if self._circuit_breaker.is_open():
            logger.error("Paused to prevent overload")
            yield {
                "type": "error",
                "message": "System overloaded, please retry",
            }
            return

        self._open_session(session_id)
        logger.info("Khởi tạo phiên làm việc thành công")

        try:
            async with asyncio.timeout(SESSION_HARD_TIMEOUT_SECONDS):
                async for event in supervisor_execute_plan(req):
                    state = self._sessions.get(session_id)
                    if state and state.status == "cancelled":
                        logger.info("Session forcefully stopped")
                        yield {"type": "error", "message": "Phiên làm việc đã bị hủy"}
                        return
                    yield event

            self._close_session(session_id, "done")
            self._circuit_breaker.record_success()
            logger.info("Phiên làm việc hoàn thành không có lỗi")

        except asyncio.TimeoutError:
            self._close_session(session_id, "timeout")
            self._circuit_breaker.record_failure()
            logger.error("Quá thời gian thực thi, phiên làm việc bị hủy")
            yield {
                "type": "error",
                "message": "Quá thời gian xử lý yêu cầu",
            }

        except asyncio.CancelledError:
            self._close_session(session_id, "cancelled")
            logger.warning("Đã hủy phiên làm việc")
            yield {
                "type": "error",
                "message": "Mất kết nối",
            }

        except Exception:
            self._close_session(session_id, "failed")
            self._circuit_breaker.record_failure()
            logger.error("Lỗi điều phối phiên làm việc")
            yield {
                "type": "error",
                "message": "Orchestration error, please retry",
            }

    def cancel_session(self, session_id: str):
        state = self._sessions.get(session_id)
        if state:
            state.status = "cancelled"
            logger.info("Đã hủy phiên làm việc theo yêu cầu")

    def get_active_sessions(self) -> list[str]:
        return list(self._sessions.keys())

    def get_circuit_status(self) -> dict:
        return {
            "is_open": self._circuit_breaker.is_open(),
            "remaining_seconds": int(self._circuit_breaker.remaining_seconds()),
        }


orchestration = OrchestrationHarness()
