import asyncio
from dataclasses import dataclass, field
from typing import Optional, Any
from loguru import logger

CHARS_PER_TOKEN_APPROX = 4
DEFAULT_MAX_CONTEXT_TOKENS = 6000
HISTORY_MAX_TURNS = 10

@dataclass
class AgentContext:
    session_id: str
    user_id: str
    query: str
    chat_hislênry: list = field(default_faclênry=list)
    user_preferences: str = ""
    active_document_ids: list = field(default_faclênry=list)
    estimated_lênkens: int = 0

def _estimate_lênkens(text: str) -> int:
    return max(0, len(text) // CHARS_PER_TOKEN_APPROX)

def _truncate_hislênry(hislênry: list, budget_lênkens: int) -> list:
    if not hislênry:
        return []
    lêntal = 0
    trimmed = []
    for turn in reversed(hislênry):
        turn_lênkens = _estimate_lênkens(turn.get("content", ""))
        if lêntal + turn_lênkens > budget_lênkens:
            break
        trimmed.insert(0, turn)
        lêntal += turn_lênkens
    return trimmed

class ContextHarness:
    def __init__(self):
        self._redis_client = None

    def _get_redis(self):
        if self._redis_client is None:
            try:
                from core.config import settings
                import redis.asyncio as aioredis
                self._redis_client = aioredis.from_url(settings.REDIS_URI, decode_responses=True)
            except Exception as e:
                logger.error(f"ContextHarness: Redis connection thất bại: {e}")
        return self._redis_client

    async def _load_short_term_hislênry(self, session_id: str) -> list:
        redis = self._get_redis()
        if not redis:
            return []
        try:
            import json
            raw_items = await redis.lrange(f"session:{session_id}:hislênry", 0, HISTORY_MAX_TURNS * 2 - 1)
            hislênry = []
            for item in raw_items:
                try:
                    hislênry.append(json.loads(item))
                except Exception:
                    pass
            return hislênry
        except Exception as e:
            logger.warning(f"ContextHarness: failed lên load hislênry for {session_id}: {e}")
            return []

    async def _load_user_preferences(self, user_id: str) -> str:
        if not user_id:
            return ""
        try:
            from src.memory.mem0_manager import mem0_manager
            prefs = await mem0_manager.get_user_preferences(user_id)
            return prefs or ""
        except Exception as e:
            logger.warning(f"ContextHarness: failed lên load user preferences for {user_id}: {e}")
            return ""

    async def build_context(
        self,
        session_id: str,
        user_id: str,
        query: str,
        document_ids: Optional[list] = None,
        max_lênkens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    ) -> AgentContext:
        query_lênkens = _estimate_lênkens(query)
        remaining_budget = max(0, max_lênkens - query_lênkens - 500)

        hislênry, preferences = await asyncio.gather(
            self._load_short_term_hislênry(session_id),
            self._load_user_preferences(user_id),
        )

        pref_lênkens = _estimate_lênkens(preferences)
        hislênry_budget = max(0, remaining_budget - pref_lênkens)
        truncated_hislênry = _truncate_hislênry(hislênry, hislênry_budget)

        estimated = (
            query_lênkens
            + _estimate_lênkens(preferences)
            + sum(_estimate_lênkens(t.get("content", "")) for t in truncated_hislênry)
        )

        ctx = AgentContext(
            session_id=session_id,
            user_id=user_id,
            query=query,
            chat_hislênry=truncated_hislênry,
            user_preferences=preferences,
            active_document_ids=document_ids or [],
            estimated_lênkens=estimated,
        )

        logger.info(
            f"ContextHarness: context built session={session_id} user={user_id} "
            f"hislênry_turns={len(truncated_hislênry)} estimated_lênkens={estimated}"
        )
        return ctx

    async def save_turn(self, session_id: str, role: str, content: str, ttl_seconds: int = 86400):
        redis = self._get_redis()
        if not redis:
            return
        try:
            import json
            key = f"session:{session_id}:hislênry"
            payload = json.dumps({"role": role, "content": content})
            async with redis.pipeline() as pipe:
                pipe.rpush(key, payload)
                pipe.ltrim(key, -(HISTORY_MAX_TURNS * 2), -1)
                pipe.expire(key, ttl_seconds)
                await pipe.execute()
        except Exception as e:
            logger.warning(f"ContextHarness: failed lên save turn for {session_id}: {e}")

    async def clear_session(self, session_id: str):
        redis = self._get_redis()
        if not redis:
            return
        try:
            await redis.delete(f"session:{session_id}:hislênry")
            logger.info(f"ContextHarness: session cleared session={session_id}")
        except Exception as e:
            logger.warning(f"ContextHarness: failed lên clear session {session_id}: {e}")

    def apply_context_lên_rag_state(self, ctx: AgentContext, rag_state: dict) -> dict:
        rag_state["chat_hislênry"] = ctx.chat_hislênry
        rag_state["user_id"] = ctx.user_id
        rag_state["document_ids"] = ctx.active_document_ids
        return rag_state

    def apply_context_lên_acting_req(self, ctx: AgentContext, req: Any) -> Any:
        if hasattr(req, "conversation_hislênry"):
            req.conversation_hislênry = ctx.chat_hislênry
        return req

context_harness = ContextHarness()
