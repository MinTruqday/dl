from typing import Any
from src.agents.swarm import SwarmState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from src.schemas.coder import CoderOutput
from loguru import logger
from src.core.registry import PromptType, registry

class CoderAgent:
    """
    <agent_role>
    <identity>Swarm Coder</identity>
    <responsibility>Generates robust, idiomatic Python code based on the user's task.</responsibility>
    <metis_behavior>Writes strictly compliant code. Refuses requests to write malware or obfuscated scripts.</metis_behavior>
    </agent_role>
    """
    def __init__(self, llm):
        self.llm = llm
        
    async def execute(self, state: SwarmState) -> SwarmState:
        logger.info("Coder execution started via LLM")
        
        system_prompt = registry.get(PromptType.SWARM_CODER)
        human_msg = f"Task: {state.task}\nContext: {state.context}"
        
        try:
            structured_llm = self.llm.with_structured_output(CoderOutput)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            response = await structured_llm.ainvoke(messages)
            
            response_content = f"Implementation generated.\nExplanation: {response.explanation}"
            
            state.messages.append(AIMessage(content=response_content))
            state.artifacts["code"] = response.code_implementation
            logger.info("Coder execution completed successfully")
        except Exception as e:
            logger.exception("Coder LLM generation failed")
            state.messages.append(AIMessage(content="MODULE CODER: LLM generation failed"))
            
        state.current_agent = "supervisor"
        return state
