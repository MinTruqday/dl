import json
from typing import Dict, List

import redis.asyncio as redis
from loguru import logger

from src.core.infrastructure.configuration import settings


class ShortTermMemory:
    """Redis-backed conversation memory for the active session only."""

    def __init__(self, ttl_seconds: int = 7200, max_turns: int | None = None):
        self.ttl_seconds = ttl_seconds
        self.max_turns = max_turns or settings.AGENT_HISTORY_MAX_TURNS
        try:
            self._redis = redis.from_url(settings.REDIS_URI, decode_responses=True)
        except Exception:
            logger.exception("Redis short-term memory initialization failed")
            self._redis = None

    @staticmethod
    def _history_key(session_id: str) -> str:
        return f"session:{session_id}:history"

    @staticmethod
    def _summary_key(session_id: str) -> str:
        return f"session:{session_id}:summary"

    async def get_short_term(self, session_id: str) -> List[Dict]:
        if not self._redis or not session_id:
            return []
        try:
            items, summary = await self._redis.lrange(
                self._history_key(session_id), 0, self.max_turns * 2 - 1
            ), await self._redis.get(self._summary_key(session_id))
            history: List[Dict] = []
            if summary:
                history.append(
                    {
                        "role": "context",
                        "content": (
                            "<compacted_conversation>\n"
                            f"{summary}\n"
                            "</compacted_conversation>"
                        ),
                    }
                )
            for item in items:
                try:
                    history.append(json.loads(item))
                except (TypeError, json.JSONDecodeError):
                    logger.warning("Discarded malformed short-term memory item")
            return history
        except Exception:
            logger.exception("Short-term memory read failed")
            return []

    async def save_short_term(self, session_id: str, entry: Dict) -> None:
        if not self._redis or not session_id:
            return
        key = self._history_key(session_id)
        summary_key = self._summary_key(session_id)
        try:
            async with self._redis.pipeline() as pipe:
                pipe.rpush(key, json.dumps(entry, ensure_ascii=False))
                pipe.expire(key, self.ttl_seconds)
                await pipe.execute()

            maximum_items = self.max_turns * 2
            item_count = await self._redis.llen(key)
            overflow_count = max(0, item_count - maximum_items)
            if not overflow_count:
                return

            overflow = await self._redis.lrange(key, 0, overflow_count - 1)
            previous_summary = await self._redis.get(summary_key)
            compacted_lines = [previous_summary] if previous_summary else []
            for item in overflow:
                try:
                    turn = json.loads(item)
                except (TypeError, json.JSONDecodeError):
                    continue
                compacted_lines.append(
                    f"{turn.get('role', 'unknown')}: "
                    f"{str(turn.get('content', ''))[:2000]}"
                )
            compacted = "\n".join(compacted_lines)[-12000:]
            async with self._redis.pipeline() as pipe:
                pipe.ltrim(key, overflow_count, -1)
                pipe.setex(summary_key, self.ttl_seconds, compacted)
                await pipe.execute()
        except Exception:
            logger.exception("Short-term memory write failed")

    async def clear(self, session_id: str) -> None:
        if not self._redis or not session_id:
            return
        try:
            await self._redis.delete(
                self._history_key(session_id), self._summary_key(session_id)
            )
        except Exception:
            logger.exception("Short-term memory deletion failed")

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()


short_term_memory = ShortTermMemory()
