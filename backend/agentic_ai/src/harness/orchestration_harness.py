import asyncio
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Optional
from core.config import settings
from loguru import logger

SESSION_HARD_TIMEOUT_SECONDS = 120
CIRCUIT_BREAKER_FAILURE_THRESHOLD = settings.CIRCUIT_BREAKER_THRESHOLD
CIRCUIT_BREAKER_RESET_SECONDS = settings.CIRCUIT_BREAKER_RESET_SECONDS

@dataclass
class SessionState:
    session_id: str
    status: Literal["running", "done", "failed", "cancelled", "timeout"] = "running"
    started_at: float = 0.0

class CircuitBreaker:
    def __init__(self, threshold: int, reset_seconds: float):
        self._failures = 0
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._tripped_at: Optional[float] = None

    def record_failure(self):
        self._failures += 1
        if self._failures >= self._threshold and not self._tripped_at:
            self._tripped_at = time.monotonic()
            logger.error("Khởi tạo AI thành công")

    def record_success(self):
        self._failures = 0
        self._tripped_at = None

    def is_open(self) -> bool:
        if not self._tripped_at:
            return False
        elapsed = time.monotonic() - self._tripped_at
        if elapsed >= self._reset_seconds:
            logger.info("Từ chối truy cập API nội bộ")
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
        self._circuit_breaker = CircuitBreaker(threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD, reset_seconds=CIRCUIT_BREAKER_RESET_SECONDS)

    def _open_session(self, session_id: str):
        self._sessions[session_id] = SessionState(session_id=session_id, status="running", started_at=time.monotonic())

    def _close_session(self, session_id: str, status: Literal["done", "failed", "cancelled", "timeout"]):
        state = self._sessions.pop(session_id, None)
        if state:
            state.status = status

    async def run(self, supervisor_execute_plan, req, session_id: str) -> AsyncGenerator[dict, None]:
        if self._circuit_breaker.is_open():
            logger.error("Từ chối truy cập API nội bộ")
            yield {"type": "error", "message": "Mất kết nối mạng tạm thời"}
            return
        self._open_session(session_id)
        logger.info("Mất kết nối mạng tạm thời")
        try:
            async with asyncio.timeout(SESSION_HARD_TIMEOUT_SECONDS):
                async for event in supervisor_execute_plan(req):
                    state = self._sessions.get(session_id)
                    if state and state.status == "cancelled":
                        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
                        yield {"type": "error", "message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}
                        return
                    yield event
            self._close_session(session_id, "done")
            self._circuit_breaker.record_success()
            logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        except asyncio.TimeoutError:
            self._close_session(session_id, "timeout")
            self._circuit_breaker.record_failure()
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            yield {"type": "error", "message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}
        except asyncio.CancelledError:
            self._close_session(session_id, "cancelled")
            logger.warning("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
            yield {"type": "error", "message": "Mất kết nối mạng tạm thời"}
        except Exception:
            self._close_session(session_id, "failed")
            self._circuit_breaker.record_failure()
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            yield {"type": "error", "message": "Mất kết nối mạng tạm thời"}

    def cancel_session(self, session_id: str):
        state = self._sessions.get(session_id)
        if state:
            state.status = "cancelled"
            logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")

    def get_active_sessions(self) -> list[str]:
        return list(self._sessions.keys())

    def get_circuit_status(self) -> dict:
        return {"is_open": self._circuit_breaker.is_open(), "remaining_seconds": int(self._circuit_breaker.remaining_seconds())}

orchestration_harness = OrchestrationHarness()