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

    async def _load_short_term_history(self, session_id: str) -> list:
        from src.memory.short_term import short_term_memory

        return await short_term_memory.get_short_term(session_id)

    async def _load_user_preferences(self, user_id: str) -> str:
        if not user_id:
            return ""
        try:
            from src.core.infrastructure.database import database
            from src.memory.management import memory_manager

            db = database.mongodb[settings.AI_DB_NAME]
            instruction_doc, memories = await asyncio.gather(
                db.user_instructions.find_one({"_id": user_id}),
                memory_manager.get_memories(user_id),
            )
            instructions = str(instruction_doc.get("instructions", "")) if instruction_doc else ""
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
                    f"<relevant_user_memory>\n{memory_text.strip()}\n</relevant_user_memory>"
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
            self._load_short_term_history(session_id), self._load_user_preferences(user_id)
        )

        preferences = preferences[: remaining_budget * CHARS_PER_TOKEN_APPROX]
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

    async def save_turn(self, session_id: str, role: str, content: str):
        from src.memory.short_term import short_term_memory

        await short_term_memory.save_short_term(session_id, {"role": role, "content": content})

    async def clear_session(self, session_id: str):
        from src.memory.short_term import short_term_memory

        await short_term_memory.clear(session_id)

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
