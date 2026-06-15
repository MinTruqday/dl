import asyncio
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Optional

from loguru import logger

SESSION_HARD_TIMEOUT_SECONDS = 120
from core.config import settings

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
            logger.error("The system circuit breaker was triggered due to multiple consecutive operational failures")

    def record_success(self):
        self._failures = 0
        self._tripped_at = None

    def is_open(self) -> bool:
        if not self._tripped_at:
            return False
        elapsed = time.monotonic() - self._tripped_at
        if elapsed >= self._reset_seconds:
            logger.info("The system circuit breaker is being reset to restore normal operational flow")
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
        self._circuit_breaker = CircuitBreaker(
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
            logger.error("The orchestration system temporarily paused the request to prevent system overload")
            yield {
                "type": "error",
                "message": "The system is currently experiencing heavy load and requires you to try again after a short waiting period",
            }
            return

        self._open_session(session_id)
        logger.info("The orchestration module successfully initialized the execution session")

        try:
            async with asyncio.timeout(SESSION_HARD_TIMEOUT_SECONDS):
                async for event in supervisor_execute_plan(req):
                    state = self._sessions.get(session_id)
                    if state and state.status == "cancelled":
                        logger.info("The active execution session was forcibly terminated by the orchestration module")
                        yield {"type": "error", "message": "The execution session was cancelled and cannot proceed further"}
                        return
                    yield event

            self._close_session(session_id, "done")
            self._circuit_breaker.record_success()
            logger.info("The execution session completed all operations successfully without any errors")

        except asyncio.TimeoutError:
            self._close_session(session_id, "timeout")
            self._circuit_breaker.record_failure()
            logger.error("The execution session exceeded the maximum allowed processing time and was terminated")
            yield {
                "type": "error",
                "message": "The request exceeded the maximum allowed processing time limit and was terminated",
            }

        except asyncio.CancelledError:
            self._close_session(session_id, "cancelled")
            logger.warning("The orchestration module detected a cancellation signal and aborted the session")
            yield {
                "type": "error",
                "message": "The session was terminated prematurely due to a loss of connection with the client",
            }

        except Exception:
            self._close_session(session_id, "failed")
            self._circuit_breaker.record_failure()
            logger.error("The orchestration module encountered an unexpected failure during the session execution")
            yield {
                "type": "error",
                "message": "The system encountered an unexpected error during the orchestration phase and requires you to try again later",
            }

    def cancel_session(self, session_id: str):
        state = self._sessions.get(session_id)
        if state:
            state.status = "cancelled"
            logger.info("The orchestration module received and processed a request to cancel the active session")

    def get_active_sessions(self) -> list[str]:
        return list(self._sessions.keys())

    def get_circuit_status(self) -> dict:
        return {
            "is_open": self._circuit_breaker.is_open(),
            "remaining_seconds": int(self._circuit_breaker.remaining_seconds()),
        }


orchestration_harness = OrchestrationHarness()