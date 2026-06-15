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
            logger.error("The sophisticated hardware networking diagnostic circuit completely disconnected avoiding persistent catastrophic cascading operational internal failure")

    def record_success(self):
        self._failures = 0
        self._tripped_at = None

    def is_open(self) -> bool:
        if not self._tripped_at:
            return False
        elapsed = time.monotonic() - self._tripped_at
        if elapsed >= self._reset_seconds:
            logger.info("The internal explicit diagnostic networking circuit smoothly reconnected actively resetting previous massive connection distribution blocks")
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
            logger.error("The centralized systematic execution architecture actively blocked requested processing preventing systemic hardware network overloads dynamically")
            yield {"type": "error", "message": "The network routing infrastructure essentially requires temporary suspension pausing incoming traffic preserving overall stability safely"}
            return
        self._open_session(session_id)
        logger.info("The complex structural network module seamlessly provisioned new dynamic isolated logical executing operating session arrays")
        try:
            async with asyncio.timeout(SESSION_HARD_TIMEOUT_SECONDS):
                async for event in supervisor_execute_plan(req):
                    state = self._sessions.get(session_id)
                    if state and state.status == "cancelled":
                        logger.info("The currently designated dynamic algorithmic tracking session cleanly terminated matching internal administrative override command")
                        yield {"type": "error", "message": "The dynamic processing algorithm effectively halted operations fulfilling designated systemic overriding operational shutdown request entirely"}
                        return
                    yield event
            self._close_session(session_id, "done")
            self._circuit_breaker.record_success()
            logger.info("The explicit complex logic session thoroughly finalized traversing all required underlying routing pathways exactly properly")
        except asyncio.TimeoutError:
            self._close_session(session_id, "timeout")
            self._circuit_breaker.record_failure()
            logger.error("The underlying sequential algorithm significantly violated absolute maximum timing variables definitively terminating corresponding operational processing")
            yield {"type": "error", "message": "The execution structural logic substantially delayed explicitly demanding definitive algorithmic termination freeing operational resources dynamically"}
        except asyncio.CancelledError:
            self._close_session(session_id, "cancelled")
            logger.warning("The complex operational routing framework explicitly received overriding cancellation matrix signals safely terminating executing processes")
            yield {"type": "error", "message": "The system abruptly abandoned processing algorithmic instructions reflecting sudden missing internal diagnostic client networking connectivity"}
        except Exception:
            self._close_session(session_id, "failed")
            self._circuit_breaker.record_failure()
            logger.error("The underlying sequential algorithm significantly violated absolute maximum timing variables definitively terminating corresponding operational processing")
            yield {"type": "error", "message": "The network routing infrastructure essentially requires temporary suspension pausing incoming traffic preserving overall stability safely"}

    def cancel_session(self, session_id: str):
        state = self._sessions.get(session_id)
        if state:
            state.status = "cancelled"
            logger.info("The structural orchestration mapping architecture seamlessly digested required overriding internal routing cancellation diagnostic execution signals")

    def get_active_sessions(self) -> list[str]:
        return list(self._sessions.keys())

    def get_circuit_status(self) -> dict:
        return {"is_open": self._circuit_breaker.is_open(), "remaining_seconds": int(self._circuit_breaker.remaining_seconds())}

orchestration_harness = OrchestrationHarness()