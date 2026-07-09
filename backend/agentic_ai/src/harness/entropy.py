import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from loguru import logger

from src.core.infrastructure.configuration import settings

ENTROPY_MESSAGE_WEIGHT = 0.3
ENTROPY_TOKEN_WEIGHT = 0.3
ENTROPY_AGE_WEIGHT = 0.2
ENTROPY_UNRESOLVED_WEIGHT = 0.2

ENTROPY_RESET_THRESHOLD = float(settings.MAX_CONTEXT_TOKENS) / 4000
ENTROPY_MAX_SESSION_AGE_SECONDS = 1800
ENTROPY_MAX_MESSAGES = 30

@dataclass
class EntropySnapshot:
    session_id: str
    entropy_score: float
    message_count: int
    estimated_tokens: int
    session_age_seconds: float
    unresolved_tool_calls: int
    should_reset: bool
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class EntropyAuditor:
    def __init__(self):
        self._session_start_times: Dict[str, float] = {}
        self._unresolved_tool_calls: Dict[str, int] = {}
        self._snapshots: Dict[str, List[EntropySnapshot]] = {}

    def register_session(self, session_id: str):
        self._session_start_times[session_id] = time.monotonic()
        self._unresolved_tool_calls[session_id] = 0
        logger.info(f"Started entropy monitoring for session {session_id}")

    def record_tool_dispatched(self, session_id: str):
        if session_id in self._unresolved_tool_calls:
            self._unresolved_tool_calls[session_id] += 1

    def record_tool_resolved(self, session_id: str):
        if session_id in self._unresolved_tool_calls:
            current = self._unresolved_tool_calls[session_id]
            self._unresolved_tool_calls[session_id] = max(0, current - 1)

    def compute_entropy(
        self,
        session_id: str,
        message_count: int,
        estimated_tokens: int,
    ) -> EntropySnapshot:
        start = self._session_start_times.get(session_id, time.monotonic())
        age_seconds = time.monotonic() - start
        unresolved = self._unresolved_tool_calls.get(session_id, 0)

        message_score = min(message_count / ENTROPY_MAX_MESSAGES, 1.0)
        token_score = min(
            estimated_tokens / settings.MAX_CONTEXT_TOKENS, 1.0
        )
        age_score = min(age_seconds / ENTROPY_MAX_SESSION_AGE_SECONDS, 1.0)
        unresolved_score = min(unresolved / 5, 1.0)

        entropy = (
            message_score * ENTROPY_MESSAGE_WEIGHT
            + token_score * ENTROPY_TOKEN_WEIGHT
            + age_score * ENTROPY_AGE_WEIGHT
            + unresolved_score * ENTROPY_UNRESOLVED_WEIGHT
        )

        should_reset = entropy >= ENTROPY_RESET_THRESHOLD

        snapshot = EntropySnapshot(
            session_id=session_id,
            entropy_score=round(entropy, 4),
            message_count=message_count,
            estimated_tokens=estimated_tokens,
            session_age_seconds=round(age_seconds, 1),
            unresolved_tool_calls=unresolved,
            should_reset=should_reset,
        )

        if session_id not in self._snapshots:
            self._snapshots[session_id] = []
        self._snapshots[session_id].append(snapshot)

        if should_reset:
            logger.warning(
                f"Session {session_id} entropy exceeded threshold: {entropy:.4f} - Reset recommended"
            )
        return snapshot

    async def reset_session(
        self,
        session_id: str,
        redis_client=None,
    ):
        logger.info(f"Started entropy reset for session {session_id}")
        try:
            if redis_client:
                await redis_client.delete(f"session:{session_id}:history")

            self._unresolved_tool_calls[session_id] = 0
            self._session_start_times[session_id] = time.monotonic()
            self._snapshots.pop(session_id, None)
            logger.info(f"Completed entropy reset for session {session_id}")
        except Exception:
            logger.exception(f"Error resetting entropy for session {session_id}")

    def should_reset(
        self,
        session_id: str,
        message_count: int,
        estimated_tokens: int,
    ) -> bool:
        snapshot = self.compute_entropy(session_id, message_count, estimated_tokens)
        return snapshot.should_reset

    def get_latest_snapshot(self, session_id: str) -> Optional[EntropySnapshot]:
        snapshots = self._snapshots.get(session_id, [])
        return snapshots[-1] if snapshots else None

    def clear_session(self, session_id: str):
        self._session_start_times.pop(session_id, None)
        self._unresolved_tool_calls.pop(session_id, None)
        self._snapshots.pop(session_id, None)

entropy = EntropyAuditor()
