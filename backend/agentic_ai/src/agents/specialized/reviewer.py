from typing import Any
from src.agents.swarm import SwarmState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from src.schemas.reviewer import ReviewerEvaluation
from loguru import logger
from src.core.registry import PromptType, registry

class ReviewerAgent:
    """
    <agent_role>
    <identity>Swarm Peer Reviewer</identity>
    <responsibility>Critiques generated code against architectural standards and coding conventions.</responsibility>
    <metis_behavior>Provides blunt, highly objective feedback. Never softens criticism with filler words.</metis_behavior>
    </agent_role>
    """
    def __init__(self, llm):
        self.llm = llm
        
    async def execute(self, state: SwarmState) -> SwarmState:
        logger.info("Reviewer execution started via LLM")
        
        code_to_review = state.artifacts.get("code", "")
        
        if not code_to_review:
            state.messages.append(AIMessage(content="Missing code artifact for evaluation"))
            state.is_complete = True
            return state
            
        system_prompt = registry.get(PromptType.SWARM_REVIEWER)
        human_msg = f"Code for review:\n{code_to_review}"
        
        try:
            structured_llm = self.llm.with_structured_output(ReviewerEvaluation)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            eval_result = await structured_llm.ainvoke(messages)
            
            review_msg = f"Code evaluation completed. Approved: {eval_result.is_approved}. Feedback: {eval_result.feedback}"
            state.messages.append(AIMessage(content=review_msg))
            state.artifacts["review"] = eval_result.feedback

            if eval_result.is_approved:
                state.is_complete = True
            logger.info("Reviewer LLM evaluation completed successfully")
        except Exception as e:
            logger.exception("Reviewer LLM evaluation failed")
            state.messages.append(AIMessage(content="MODULE REVIEWER: LLM evaluation failed"))
            state.is_complete = True
            
        state.current_agent = "supervisor"
        return state
