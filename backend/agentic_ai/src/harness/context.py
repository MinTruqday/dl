import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from src.core.infrastructure.configuration import settings

CHARS_PER_TOKEN_APPROX = 4
DEFAULT_MAX_CONTEXT_TOKENS = settings.AGENT_MAX_CONTEXT_TOKENS
HISTORY_MAX_TURNS = settings.AGENT_HISTORY_MAX_TURNS

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
    """
    <module_purpose>
    <purpose>Manages shared context windows for multi-agent interactions.</purpose>
    <metis_behavior>Strictly isolates context boundaries between different user sessions.</metis_behavior>
    </module_purpose>
    """
    def __init__(self):
        self._redis_client = None

    def _get_redis(self):
        if self._redis_client is None:
            try:
                import redis.asyncio as aioredis

                from src.core.infrastructure.configuration import settings

                self._redis_client = aioredis.from_url(
                    settings.REDIS_URI, decode_responses=True
                )
            except Exception:
                logger.exception("Redis connection error")
        return self._redis_client

    async def _load_short_term_history(self, session_id: str) -> list:
        redis = self._get_redis()
        if not redis:
            return []
        try:
            import json

            history_key = f"session:{session_id}:history"
            summary_key = f"session:{session_id}:summary"
            raw_items, summary = await asyncio.gather(
                redis.lrange(history_key, 0, HISTORY_MAX_TURNS * 2 - 1),
                redis.get(summary_key),
            )
            history = []
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
            for item in raw_items:
                try:
                    history.append(json.loads(item))
                except (TypeError, json.JSONDecodeError):
                    logger.warning("Discarded malformed short term history item")
            return history
        except Exception:
            logger.exception("Error loading chat history from temporary storage")
            return []

    async def _load_user_preferences(self, user_id: str) -> str:
        if not user_id:
            return ""
        try:
            from src.core.infrastructure.database import database
            from src.memory.management import memory_manager

            db = database.mongodb[settings.AGENTIC_AI_DB_NAME]
            instruction_doc, memories = await asyncio.gather(
                db.user_instructions.find_one({"_id": user_id}),
                memory_manager.get_memories(user_id),
            )
            instructions = (
                str(instruction_doc.get("instructions", ""))
                if instruction_doc
                else ""
            )
            memory_text = memories or ""
            sections = []
            if instructions.strip():
                sections.append(
                    "<persistent_user_instructions>\n"
                    f"{instructions.strip()}\n"
                    "</persistent_user_instructions>"
                )
            if memory_text.strip():
                sections.append(
                    "<relevant_user_memory>\n"
                    f"{memory_text.strip()}\n"
                    "</relevant_user_memory>"
                )
            return "\n\n".join(sections)
        except Exception:
            logger.exception("Error loading personal configuration")
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

        preferences = preferences[
            : remaining_budget * CHARS_PER_TOKEN_APPROX
        ]
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

        logger.info("Context data compiled")
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
            summary_key = f"session:{session_id}:summary"
            payload = json.dumps({"role": role, "content": content})
            async with redis.pipeline() as pipe:
                pipe.rpush(key, payload)
                pipe.expire(key, ttl_seconds)
                await pipe.execute()
            maximum_items = HISTORY_MAX_TURNS * 2
            item_count = await redis.llen(key)
            overflow_count = max(0, item_count - maximum_items)
            if overflow_count:
                overflow, previous_summary = await asyncio.gather(
                    redis.lrange(key, 0, overflow_count - 1),
                    redis.get(summary_key),
                )
                compacted_lines = []
                if previous_summary:
                    compacted_lines.append(previous_summary)
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
                async with redis.pipeline() as pipe:
                    pipe.ltrim(key, overflow_count, -1)
                    pipe.setex(summary_key, ttl_seconds, compacted)
                    await pipe.execute()
        except Exception:
            logger.exception("Error saving interaction session")

    async def clear_session(self, session_id: str):
        redis = self._get_redis()
        if not redis:
            return
        try:
            await redis.delete(f"session:{session_id}:history")
            await redis.delete(f"session:{session_id}:summary")
            logger.info("Session history deleted")
        except Exception:
            logger.exception("Error deleting session from memory")

    def apply_context_to_rag_state(self, ctx: AgentContext, rag_state: dict) -> dict:
        rag_state["chat_history"] = ctx.chat_history
        rag_state["user_id"] = ctx.user_id
        rag_state["document_ids"] = ctx.active_document_ids
        return rag_state

    def apply_context_to_acting_req(self, ctx: AgentContext, req: Any) -> Any:
        if hasattr(req, "conversation_history"):
            req.conversation_history = ctx.chat_history
        return req

context = ContextHarness()
