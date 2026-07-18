from __future__ import annotations

import re
from typing import Dict, List, Optional

from loguru import logger

from src.proactive.bank import MemoryBank, ProactiveMemoryBank, proactive_memory_bank


_WINDOW_SIZE = 8
_INTERVENTION_TAG = "context_for_action"
_NO_INTERVENTION_TAG = "no_intervention"


def _format_trajectory_window(trajectory: List[Dict], window: int = _WINDOW_SIZE) -> str:
    """Render the last `window` trajectory turns as compact text."""
    recent = trajectory[-window:]
    lines: List[str] = []
    for i, turn in enumerate(recent):
        role = turn.get("role", "unknown").upper()
        content = str(turn.get("content", ""))
        if len(content) > 600:
            content = content[:300] + "\n[...TRUNCATED...]\n" + content[-300:]
        lines.append(f"[TURN {i + 1}] {role}: {content}")
    return "\n".join(lines) if lines else "(no trajectory)"


def _parse_phase1_tool_calls(raw_output: str) -> List[Dict]:
    pattern = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)
    calls = []
    for match in pattern.finditer(raw_output):
        try:
            import json
            call = json.loads(match.group(1).strip())
            if isinstance(call, dict) and "name" in call:
                calls.append(call)
        except Exception:
            logger.warning("ProactiveMemoryAgent Phase 1 failed to parse tool call block")
    return calls


def _parse_phase2_output(raw_output: str) -> Optional[str]:
    if f"<{_NO_INTERVENTION_TAG}" in raw_output:
        return None

    match = re.search(
        rf"<{_INTERVENTION_TAG}>(.*?)</{_INTERVENTION_TAG}>",
        raw_output,
        re.DOTALL,
    )
    if match:
        text = match.group(1).strip()
        return text if text else None

    return None


class ProactiveMemoryAgent:
    """
    <module_purpose>
    <purpose>Two-phase Memory Agent that runs alongside action agents without modifying them.</purpose>
    <design>
    Phase 1 — Bank Management:
      Observes recent trajectory window and current memory bank.
      Issues structured tool calls to update the bank (save_knowledge, save_procedural,
      update_status, delete). Does not touch the action agent.

    Phase 2 — Intervention Decision:
      Reads the updated bank and trajectory window.
      Emits either a targeted <context_for_action> reminder or <no_intervention/>.
      The reminder is injected into the next action-agent call as transient context.
    </design>
    </module_purpose>
    <contract>
    - Precondition: HuggingFace LLM endpoint configured via settings.
    - Postcondition: Returns Optional[str] — None means no intervention this step.
    - Error Handling: Any LLM failure in either phase is caught; pipeline is not interrupted.
    </contract>
    """

    def __init__(self, bank: Optional[ProactiveMemoryBank] = None) -> None:
        self._bank = bank or proactive_memory_bank

    def _build_llm(self):
        from huggingface_hub import AsyncInferenceClient
        from src.core.infrastructure.configuration import settings
        from src.utils.huggingface import HFInferenceChat

        client = AsyncInferenceClient(model=settings.LLM_MODEL, token=settings.HF_TOKEN)
        return HFInferenceChat(client=client, model=settings.LLM_MODEL)

    async def _run_phase1(
        self,
        session_id: str,
        task_description: str,
        trajectory_window: str,
        bank: MemoryBank,
    ) -> MemoryBank:
        from langchain_core.messages import HumanMessage, SystemMessage
        from src.core.registry import PromptType, registry

        bank_snapshot = self._bank.format_bank_snapshot(bank)
        phase1_system = registry.get(PromptType.MEMORY_BANK_PHASE1)
        phase1_user = (
            f"<task>\n{task_description}\n</task>\n\n"
            f"<recent_trajectory>\n{trajectory_window}\n</recent_trajectory>\n\n"
            f"<current_bank>\n{bank_snapshot}\n</current_bank>\n\n"
            "Issue the appropriate memory tool calls based on the above."
        )

        try:
            llm = self._build_llm()
            response = await llm.ainvoke(
                [
                    SystemMessage(content=phase1_system),
                    HumanMessage(content=phase1_user),
                ],
                max_tokens=1024,
                temperature=0.1,
            )
            raw = response.content
            tool_calls = _parse_phase1_tool_calls(raw)
            logger.info(
                f"ProactiveMemoryAgent Phase 1 produced {len(tool_calls)} tool call(s) for session={session_id}"
            )

            for call in tool_calls:
                name = call.get("name", "")
                args = call.get("args", {})
                await self._dispatch_tool(session_id, name, args)

        except Exception:
            logger.exception(
                f"ProactiveMemoryAgent Phase 1 LLM call failed for session={session_id}"
            )

        return await self._bank.get_bank(session_id)

    async def _dispatch_tool(
        self, session_id: str, name: str, args: Dict
    ) -> None:
        try:
            if name == "memory_update_status":
                await self._bank.update_status(session_id, args.get("status", ""))

            elif name == "memory_save_knowledge":
                from src.memory.mem0_client import mem0_manager
                await self._bank.save_knowledge(
                    session_id,
                    entry_id=args.get("id", ""),
                    content=args.get("content", ""),
                    category=args.get("category", "task_fact"),
                )
                await mem0_manager.add_memory(session_id, args.get("content", ""), metadata={"category": args.get("category", "task_fact")})

            elif name == "memory_save_procedural":
                await self._bank.save_procedural(
                    session_id,
                    entry_id=args.get("id", ""),
                    content=args.get("content", ""),
                    category=args.get("category", "attempt"),
                )

            elif name == "memory_delete":
                await self._bank.delete_entry(session_id, entry_id=args.get("id", ""))

            else:
                logger.warning(
                    f"ProactiveMemoryAgent unknown tool call name='{name}' ignored"
                )
        except Exception:
            logger.exception(
                f"ProactiveMemoryAgent tool dispatch failed name={name} session={session_id}"
            )

    async def _run_phase2(
        self,
        session_id: str,
        task_description: str,
        trajectory_window: str,
        bank: MemoryBank,
    ) -> Optional[str]:
        from langchain_core.messages import HumanMessage, SystemMessage
        from src.core.registry import PromptType, registry

        bank_snapshot = self._bank.format_bank_snapshot(bank)

        if bank_snapshot == "(empty bank)":
            logger.info(
                f"ProactiveMemoryAgent Phase 2 skipped: empty bank for session={session_id}"
            )
            return None

        phase2_system = registry.get(PromptType.MEMORY_BANK_PHASE2)
        phase2_user = (
            f"<task>\n{task_description}\n</task>\n\n"
            f"<recent_trajectory>\n{trajectory_window}\n</recent_trajectory>\n\n"
            f"<memory_bank>\n{bank_snapshot}\n</memory_bank>\n\n"
            "Decide whether to intervene. Emit ONLY one of the two tags."
        )

        try:
            llm = self._build_llm()
            response = await llm.ainvoke(
                [
                    SystemMessage(content=phase2_system),
                    HumanMessage(content=phase2_user),
                ],
                max_tokens=512,
                temperature=0.1,
            )
            raw = response.content
            intervention = _parse_phase2_output(raw)

            if intervention:
                logger.info(
                    f"ProactiveMemoryAgent Phase 2 intervention fired for session={session_id}"
                )
            else:
                logger.info(
                    f"ProactiveMemoryAgent Phase 2 stayed silent for session={session_id}"
                )

            return intervention

        except Exception:
            logger.exception(
                f"ProactiveMemoryAgent Phase 2 LLM call failed for session={session_id}"
            )
            return None

    async def run(
        self,
        session_id: str,
        task_description: str,
        trajectory: List[Dict],
    ) -> Optional[str]:
        trajectory_window = _format_trajectory_window(trajectory)

        current_bank = await self._bank.get_bank(session_id)

        updated_bank = await self._run_phase1(
            session_id, task_description, trajectory_window, current_bank
        )

        intervention = await self._run_phase2(
            session_id, task_description, trajectory_window, updated_bank
        )

        return intervention

proactive_memory_agent = ProactiveMemoryAgent()
