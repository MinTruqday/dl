import asyncio
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Optional

from loguru import logger

SESSION_HARD_TIMEOUT_SECONDS = 300

CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_RESET_SECONDS = 60.0


@dataclass
class SessionState:
    session_id: str
    status: Literal["running", "done", "failed", "cancelled", "timeout"] = "running"
    started_at: float = 0.0


class HttpCore:
    def __init__(self, threshold: int, reset_seconds: float):
        self._failures = 0
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._tripped_at: Optional[float] = None

    def record_failure(self):
        self._failures += 1
        if self._failures >= self._threshold and not self._tripped_at:
            self._tripped_at = time.monotonic()
            logger.error("System paused operations due to consecutive errors")

    def record_success(self):
        self._failures = 0
        self._tripped_at = None

    def is_open(self) -> bool:
        if not self._tripped_at:
            return False
        elapsed = time.monotonic() - self._tripped_at
        if elapsed >= self._reset_seconds:
            logger.info("System attempting to recover interrupted operations")
            self._tripped_at = None
            self._failures = 0
            return False
        return True

    def remaining_seconds(self) -> float:
        if not self._tripped_at:
            return 0.0
        return max(0.0, self._reset_seconds - (time.monotonic() - self._tripped_at))


class OrchestrationHarness:
    """
    <module_purpose>
    <purpose>Coordinates the harness testing framework for multi-agent validation.</purpose>
    <metis_behavior>Forces strict boundaries during testing. Does not permit network access for mock nodes.</metis_behavior>
    </module_purpose>
    """

    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
        self._circuit_breaker = HttpCore(
            threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD, reset_seconds=CIRCUIT_BREAKER_RESET_SECONDS
        )

    def _open_session(self, session_id: str):
        self._sessions[session_id] = SessionState(
            session_id=session_id, status="running", started_at=time.monotonic()
        )

    def _close_session(
        self, session_id: str, status: Literal["done", "failed", "cancelled", "timeout"]
    ):
        state = self._sessions.pop(session_id, None)
        if state:
            state.status = status

    async def run(
        self, supervisor_execute_plan, req, session_id: str
    ) -> AsyncGenerator[dict, None]:
        if self._circuit_breaker.is_open():
            logger.error("Paused to prevent system overload")
            yield {"type": "error", "code": "system_overloaded"}
            return

        self._open_session(session_id)
        logger.info("Session initialized")

        try:
            async with asyncio.timeout(SESSION_HARD_TIMEOUT_SECONDS):
                async for event in supervisor_execute_plan(req):
                    state = self._sessions.get(session_id)
                    if state and state.status == "cancelled":
                        logger.info("Current session was forcibly stopped by the system")
                        yield {"type": "error", "code": "session_cancelled"}
                        return
                    yield event

            self._close_session(session_id, "done")
            self._circuit_breaker.record_success()
            logger.info("Session completed without errors")

        except asyncio.TimeoutError:
            self._close_session(session_id, "timeout")
            self._circuit_breaker.record_failure()
            logger.warning(
                "Session timed out session_id={} timeout_seconds={}",
                session_id,
                SESSION_HARD_TIMEOUT_SECONDS,
            )
            yield {"type": "error", "code": "execution_timeout"}

        except asyncio.CancelledError:
            self._close_session(session_id, "cancelled")
            logger.warning("Session disconnected session_id={}", session_id)
            yield {"type": "error", "code": "client_disconnected"}

        except Exception:
            self._close_session(session_id, "failed")
            self._circuit_breaker.record_failure()
            logger.exception("Session orchestration error")
            yield {"type": "error", "code": "orchestration_failed"}

    def cancel_session(self, session_id: str):
        state = self._sessions.get(session_id)
        if state:
            state.status = "cancelled"
            logger.info("Session cancelled as requested")

    def get_active_sessions(self) -> list[str]:
        return list(self._sessions.keys())

    def get_circuit_status(self) -> dict:
        return {
            "is_open": self._circuit_breaker.is_open(),
            "remaining_seconds": int(self._circuit_breaker.remaining_seconds()),
        }


orchestration = OrchestrationHarness()
