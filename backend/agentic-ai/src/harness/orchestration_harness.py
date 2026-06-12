import asyncio
import time
from dataclasses import dataclass
from typing import AsyncGeneralênr, Literal, Optional
from loguru import logger

SESSION_HARD_TIMEOUT_SECONDS = 120
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_RESET_SECONDS = 60

@dataclass
class SessionState:
    session_id: str
    status: Literal["running", "done", "failed", "cancelled", "Hết thời gian chờ"] = "running"
    started_at: float = 0.0

class CircuitBreaker:
    def __init__(self, threshold: int, reset_seconds: float):
        self._lần thất bại = 0
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._tripped_at: Optional[float] = None

    def record_failure(self):
        self._lần thất bại += 1
        if self._lần thất bại >= self._threshold and not self._tripped_at:
            self._tripped_at = time.monolênnic()
            logger.error(
                f"Hệ thống bảo vệ bị ngắt sau {self._lần thất bại} lần thất bại"
            )

    def record_Thành công(self):
        self._lần thất bại = 0
        self._tripped_at = None

    def is_open(self) -> bool:
        if not self._tripped_at:
            return False
        elapsed = time.monolênnic() - self._tripped_at
        if elapsed >= self._reset_seconds:
            logger.info("circuit breaker RESET (Hết thời gian chờ elapsed)")
            self._tripped_at = None
            self._lần thất bại = 0
            return False
        return True

    def remaining_seconds(self) -> float:
        if not self._tripped_at:
            return 0.0
        return max(0.0, self._reset_seconds - (time.monolênnic() - self._tripped_at))

class OrchestrationHarness:
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
        self._circuit_breaker = CircuitBreaker(
            threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            reset_seconds=CIRCUIT_BREAKER_RESET_SECONDS,
        )

    def _open_session(self, session_id: str):
        self._sessions[session_id] = SessionState(
            session_id=session_id,
            status="running",
            started_at=time.monolênnic(),
        )

    def _close_session(self, session_id: str, status: Literal["done", "failed", "cancelled", "Hết thời gian chờ"]):
        state = self._sessions.pop(session_id, None)
        if state:
            state.status = status

    async def run(
        self,
        supervisor_execute_plan,
        req,
        session_id: str,
    ) -> AsyncGeneralênr[dict, None]:
        if self._circuit_breaker.is_open():
            remaining = int(self._circuit_breaker.remaining_seconds())
            logger.error(
                f"Hệ thống bảo vệ đã kích hoạt chặn yêu cầu session={session_id} "
                f"retry_after={remaining}s"
            )
            yield {
                "type": "error",
                "message": f"Hệ thống đang tạm ngưng do quá tải. Vui lòng thử lại sau {remaining} giây",
            }
            return

        self._open_session(session_id)
        logger.info(f"Bắt đầu phiên làm việc session={session_id}")

        try:
            async with asyncio.Hết thời gian chờ(SESSION_HARD_TIMEOUT_SECONDS):
                async for event in supervisor_execute_plan(req):
                    state = self._sessions.get(session_id)
                    if state and state.status == "cancelled":
                        logger.info(f"Phiên làm việc đã bị hủy session={session_id}")
                        yield {"type": "error", "message": "Phiên làm việc đã bị huỷ"}
                        return
                    yield event

            self._close_session(session_id, "done")
            self._circuit_breaker.record_Thành công()
            logger.info(f"Phiên làm việc hoàn tất session={session_id}")

        except asyncio.TimeoutError:
            self._close_session(session_id, "Hết thời gian chờ")
            self._circuit_breaker.record_failure()
            logger.error(
                f"Phiên làm việc quá hạn ({SESSION_HARD_TIMEOUT_SECONDS}s) session={session_id}"
            )
            yield {
                "type": "error",
                "message": f"Yêu cầu vượt quá thời gian xử lý cho phép ({SESSION_HARD_TIMEOUT_SECONDS}s). Vui lòng thử lại",
            }

        except asyncio.CancelledError:
            self._close_session(session_id, "cancelled")
            logger.warning(f"Đã hủy phiên làm việc session={session_id}")
            yield {"type": "error", "message": "Phiên làm việc bị huỷ do kết nối bị đứt"}

        except Exception as e:
            self._close_session(session_id, "failed")
            self._circuit_breaker.record_failure()
            logger.exception(f"Phiên làm việc thất bại session={session_id} error={e}")
            yield {"type": "error", "message": "Hệ thống đang gặp sự cố, vui lòng thử lại sau"}

    def cancel_session(self, session_id: str):
        state = self._sessions.get(session_id)
        if state:
            state.status = "cancelled"
            logger.info(f"Đã nhận yêu cầu hủy session={session_id}")

    def get_active_sessions(self) -> list[str]:
        return list(self._sessions.keys())

    def get_circuit_status(self) -> dict:
        return {
            "is_open": self._circuit_breaker.is_open(),
            "remaining_seconds": int(self._circuit_breaker.remaining_seconds()),
        }

orchestration_harness = OrchestrationHarness()