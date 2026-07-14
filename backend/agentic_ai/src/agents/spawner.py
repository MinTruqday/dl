from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger


class SpawnedAgent:
    """
    <module_purpose>
        <purpose>Execute a highly specific, short-lived task using a custom system prompt generated at runtime.</purpose>
        <context>Instantiated on-the-fly by AgentSpawner when a swarm needs a specialized, temporary role (e.g., specific framework expert) that is not part of the standard core agents.</context>
    </module_purpose>
    
    <contract>
        <input>Requires an instantiated LLM client, a role description (str), and a specialized system_prompt (str).</input>
        <output>Executes tasks and returns text artifacts.</output>
        <exceptions>Returns an error string starting with MODULE SPAWNED_AGENT if LLM invocation fails.</exceptions>
    </contract>
    """

    def __init__(self, llm, role: str, system_prompt: str):
        self.llm = llm
        self.role = role
        self.system_prompt = system_prompt

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.llm = None
        self.system_prompt = None

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
        <purpose>Enable SwarmAgent to dynamically create and orchestrate new, specialized sub-agents at runtime.</purpose>
        <context>Used by SwarmAgent or other orchestrators when they encounter a task requiring domain expertise not covered by statically defined agents.</context>
    </module_purpose>
    
    <contract>
        <input>Requires an instantiated LLM client.</input>
        <output>Manages the lifecycle of SpawnedAgent instances, ensuring clean memory release via async context managers.</output>
        <exceptions>None directly; delegates execution errors to SpawnedAgent output.</exceptions>
    </contract>
    """

    def __init__(self, llm):
        self.llm = llm

    async def _generate_system_prompt(self, role: str) -> str:
        logger.info(f"Generating system prompt for spawned role: {role}")
        from src.core.registry import PromptType, registry
        meta_prompt = registry.get(PromptType.SPAWNER_SYSTEM).format(role=role)
        try:
            response = await self.llm.ainvoke([HumanMessage(content=meta_prompt)])
            return response.content.strip()
        except Exception:
            logger.exception("System prompt generation for spawned agent failed")
            return f"<system_identity>\nYou are a highly specialized expert in {role}.\n</system_identity>\n<objective>\nComplete the given task with precision and depth.\n</objective>"

    async def spawn(self, role: str, task: str) -> str:
        system_prompt = await self._generate_system_prompt(role)
        async with SpawnedAgent(llm=self.llm, role=role, system_prompt=system_prompt) as agent:
            return await agent.run(task)
