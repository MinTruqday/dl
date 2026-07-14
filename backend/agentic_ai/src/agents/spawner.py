from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger


class SpawnedAgent:
    """
    <agent_role>
    <identity>Dynamically spawned sub-agent</identity>
    <responsibility>Executes a highly specific task using a custom system prompt generated at runtime.</responsibility>
    <metis_behavior>Acts as a stateless worker. Receives a task, executes it via LLM with a role-specific system prompt, and returns the result as a string artifact.</metis_behavior>
    </agent_role>
    """

    def __init__(self, llm, role: str, system_prompt: str):
        self.llm = llm
        self.role = role
        self.system_prompt = system_prompt

    async def run(self, task: str) -> str:
        logger.info(f"Spawned agent '{self.role}' execution started")
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=task),
        ]
        try:
            response = await self.llm.ainvoke(messages)
            logger.info(f"Spawned agent '{self.role}' execution completed successfully")
            return response.content.strip()
        except Exception:
            logger.exception(f"Spawned agent '{self.role}' execution failed")
            return f"MODULE SPAWNED_AGENT({self.role}): Execution failed"


class AgentSpawner:
    """
    <module_purpose>
    <purpose>Enables SwarmAgent to create new specialized sub-agents at runtime based on the task requirement.</purpose>
    <metis_behavior>Generates a role-specific system prompt via LLM, instantiates a SpawnedAgent, executes the task, and returns the result as a string. Does not persist agent instances beyond the call.</metis_behavior>
    </module_purpose>
    """

    def __init__(self, llm):
        self.llm = llm

    async def _generate_system_prompt(self, role: str) -> str:
        logger.info(f"Generating system prompt for spawned role: {role}")
        meta_prompt = (
            f"You are a prompt engineer. Write a concise, professional system prompt for an AI agent "
            f"with the role: '{role}'. The agent must be highly focused, expert-level, and produce "
            f"structured, actionable outputs. Output only the system prompt text."
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=meta_prompt)])
            return response.content.strip()
        except Exception:
            logger.exception("System prompt generation for spawned agent failed")
            return f"You are a highly specialized expert in {role}. Complete the given task with precision and depth."

    async def spawn(self, role: str, task: str) -> str:
        system_prompt = await self._generate_system_prompt(role)
        agent = SpawnedAgent(llm=self.llm, role=role, system_prompt=system_prompt)
        return await agent.run(task)
