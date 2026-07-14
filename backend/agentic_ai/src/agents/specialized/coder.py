from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from loguru import logger

from src.agents.swarm import SwarmState
from src.core.registry import PromptType, registry
from src.schemas.coder import CoderOutput


class CoderAgent:
    """
    <agent_role>
    <identity>Swarm Coder</identity>
    <responsibility>Generates robust, idiomatic Python code based on the user's task. Delegates to spawned sub-agents when the task requires a specialized role.</responsibility>
    <metis_behavior>Writes strictly compliant code. Refuses requests to write malware or obfuscated scripts. Supports dynamic sub-agent spawning via [SPAWN:role] task prefix.</metis_behavior>
    </agent_role>
    """

    def __init__(self, llm):
        self.llm = llm

    async def execute(self, state: SwarmState) -> SwarmState:
        logger.info("Coder execution started via LLM")

        task = state.task
        if task.startswith("[SPAWN:"):
            end_bracket = task.find("]")
            if end_bracket > 7:
                role = task[7:end_bracket]
                spawn_task = task[end_bracket + 1:].strip()
                from src.agents.spawner import AgentSpawner
                spawner = AgentSpawner(self.llm)
                result = await spawner.spawn(role, spawn_task)
                state.messages.append(AIMessage(content=f"Spawned agent '{role}' completed task"))
                state.artifacts["code"] = result
                state.current_agent = "supervisor"
                return state

        system_prompt = registry.get(PromptType.SWARM_CODER)
        human_msg = f"Task: {task}\nContext: {state.context}"

        try:
            structured_llm = self.llm.with_structured_output(CoderOutput)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            response = await structured_llm.ainvoke(messages)

            response_content = f"Implementation generated.\nExplanation: {response.explanation}"
            state.messages.append(AIMessage(content=response_content))
            state.artifacts["code"] = response.code_implementation
            logger.info("Coder execution completed successfully")
        except Exception:
            logger.exception("Coder LLM generation failed")
            state.messages.append(AIMessage(content="MODULE CODER: LLM generation failed"))

        state.current_agent = "supervisor"
        return state
