from __future__ import annotations

from typing import Dict, List, Optional

from loguru import logger

from src.proactive.agent import proactive_memory_agent

_TRIGGER_INTERVAL = 5
_MEMORY_CONTEXT_WRAP_OPEN = "<memory_context>"
_MEMORY_CONTEXT_WRAP_CLOSE = "</memory_context>"


def _should_trigger(step_count: int, force_on_failure: bool = False) -> bool:
    if step_count <= 1:
        return True
    if force_on_failure:
        return True
    return step_count % _TRIGGER_INTERVAL == 0


def wrap_memory_context(reminder: str) -> str:
    return f"{_MEMORY_CONTEXT_WRAP_OPEN}\n{reminder}\n{_MEMORY_CONTEXT_WRAP_CLOSE}"


class MemoryMiddleware:
    """
    <module_purpose>
    <purpose>Plug-and-play middleware that wires the ProactiveMemoryAgent into any action-agent pipeline.</purpose>
    <design>
    Called once per step before the action agent runs.
    Evaluates the trigger condition, runs the two-phase memory agent if triggered,
    and returns either a wrapped context string for injection or None.

    The action agent is never modified — memory context is passed as an optional parameter
    at call time. If the memory pipeline fails for any reason, the action agent proceeds
    normally without interruption.
    </design>
    </module_purpose>
    <contract>
    - Precondition: session_id, trajectory list, step count, and task description are provided.
    - Postcondition: Returns Optional[str] — None if no intervention, wrapped reminder if intervening.
    - Error Handling: All exceptions inside the memory pipeline are swallowed; never crashes the caller.
    </contract>
    """

    async def process(
        self,
        session_id: str,
        trajectory: List[Dict],
        step_count: int,
        task_description: str,
        force_on_failure: bool = False,
        user_id: str = "",
    ) -> Optional[str]:
        if not _should_trigger(step_count, force_on_failure):
            return None

        try:
            logger.info(
                f"MemoryMiddleware triggered at step={step_count} session={session_id}"
            )

            reminder = await proactive_memory_agent.run(
                session_id=session_id,
                task_description=task_description,
                trajectory=trajectory,
                user_id=user_id,
            )

            if reminder:
                logger.info(
                    f"MemoryMiddleware injecting context at step={step_count} session={session_id}"
                )
                return wrap_memory_context(reminder)

            return None

        except Exception:
            logger.exception(
                f"MemoryMiddleware pipeline error at step={step_count} session={session_id} — action agent proceeds normally"
            )
            return None


memory_middleware = MemoryMiddleware()
