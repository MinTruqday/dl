import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

CHARS_PER_TOKEN_APPROX = 4
DEFAULT_MAX_CONTEXT_TOKENS = 6000
HISTORY_MAX_TURNS = 10


@dataclass
class AgentContext:
    session_id: str
    user_id: str
    query: str
    chat_history: list = field(default_factory=list)
    user_preferences: str = ""
    active_document_ids: list = field(default_factory=list)
    estimated_tokens: int = 0


def _estimate_tokens(text: str) -> int:
    return max(0, len(text) // CHARS_PER_TOKEN_APPROX)


def _truncate_history(history: list, budget_tokens: int) -> list:
    if not history:
        return []
    total = 0
    trimmed = []
    for turn in reversed(history):
        turn_tokens = _estimate_tokens(turn.get("content", ""))
        if total + turn_tokens > budget_tokens:
            break
        trimmed.insert(0, turn)
        total += turn_tokens
    return trimmed


class ContextHarness:
    def __init__(self):
        self._redis_client = None

    def _get_redis(self):
        if self._redis_client is None:
            try:
                import redis.asyncio as aioredis
                from core.config import settings

                self._redis_client = aioredis.from_url(
                    settings.REDIS_URI, decode_responses=True
                )
            except Exception as e:
                logger.error("Lỗi kết nối bộ nhớ đệm")
        return self._redis_client

    async def _load_short_term_history(self, session_id: str) -> list:
        redis = self._get_redis()
        if not redis:
            return []
        try:
            import json

            raw_items = await redis.lrange(
                f"session:{session_id}:history", 0, HISTORY_MAX_TURNS * 2 - 1
            )
            history = []
            for item in raw_items:
                try:
                    history.append(json.loads(item))
                except Exception:
                    pass
            return history
        except Exception as e:
            logger.warning("Lỗi tải lịch sử phiên làm việc")
            return []

    async def _load_user_preferences(self, user_id: str) -> str:
        if not user_id:
            return ""
        try:
            from src.memory.mem0_manager import mem0_manager

            prefs = await mem0_manager.get_user_preferences(user_id)
            return prefs or ""
        except Exception as e:
            logger.warning("Lỗi tải cài đặt người dùng")
            return ""

    async def build_context(
        self,
        session_id: str,
        user_id: str,
        query: str,
        document_ids: Optional[list] = None,
        max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    ) -> AgentContext:
        query_tokens = _estimate_tokens(query)
        remaining_budget = max(0, max_tokens - query_tokens - 500)

        history, preferences = await asyncio.gather(
            self._load_short_term_history(session_id),
            self._load_user_preferences(user_id),
        )

        pref_tokens = _estimate_tokens(preferences)
        history_budget = max(0, remaining_budget - pref_tokens)
        truncated_history = _truncate_history(history, history_budget)

        estimated = (
            query_tokens
            + _estimate_tokens(preferences)
            + sum(_estimate_tokens(t.get("content", "")) for t in truncated_history)
        )

        ctx = AgentContext(
            session_id=session_id,
            user_id=user_id,
            query=query,
            chat_history=truncated_history,
            user_preferences=preferences,
            active_document_ids=document_ids or [],
            estimated_tokens=estimated,
        )

        logger.info("Xây dựng ngữ cảnh hoàn tất")
        return ctx

    async def save_turn(
        self, session_id: str, role: str, content: str, ttl_seconds: int = 86400
    ):
        redis = self._get_redis()
        if not redis:
            return
        try:
            import json

            key = f"session:{session_id}:history"
            payload = json.dumps({"role": role, "content": content})
            async with redis.pipeline() as pipe:
                pipe.rpush(key, payload)
                pipe.ltrim(key, -(HISTORY_MAX_TURNS * 2), -1)
                pipe.expire(key, ttl_seconds)
                await pipe.execute()
        except Exception as e:
            logger.warning("Lỗi lưu tương tác phiên làm việc")

    async def clear_session(self, session_id: str):
        redis = self._get_redis()
        if not redis:
            return
        try:
            await redis.delete(f"session:{session_id}:history")
            logger.info("Đã xóa phiên làm việc")
        except Exception as e:
            logger.warning("Lỗi xóa phiên làm việc")

    def apply_context_to_rag_state(self, ctx: AgentContext, rag_state: dict) -> dict:
        rag_state["chat_history"] = ctx.chat_history
        rag_state["user_id"] = ctx.user_id
        rag_state["document_ids"] = ctx.active_document_ids
        return rag_state

    def apply_context_to_acting_req(self, ctx: AgentContext, req: Any) -> Any:
        if hasattr(req, "conversation_history"):
            req.conversation_history = ctx.chat_history
        return req


context_harness = ContextHarness()
