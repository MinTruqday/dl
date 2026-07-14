from typing import Any, List
from src.agents.swarm import SwarmState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from loguru import logger
from src.core.registry import PromptType, registry

class SecOpsEvaluation(BaseModel):
    is_secure: bool = Field(..., description="True if no critical vulnerabilities found.")
    vulnerability_summary: str = Field(..., description="Summary of vulnerabilities.")

class SecOpsAgent:
    """
    <agent_role>
    <identity>Swarm Security Operations</identity>
    <responsibility>Analyzes generated code using SAST tools to ensure absolute security compliance.</responsibility>
    <metis_behavior>Acts as an unforgiving gatekeeper. Fails any code containing hardcoded secrets or injection vectors.</metis_behavior>
    </agent_role>
    """
    def __init__(self, llm, sast_tools=None):
        self.llm = llm
        self.sast_tools = sast_tools or []
        
    async def execute(self, state: SwarmState) -> SwarmState:
        logger.info("SecOps execution started via LLM")
        
        code_to_review = state.artifacts.get("code", "")
        if not code_to_review:
            state.messages.append(AIMessage(content="MODULE SECOPS: Missing code artifact for scanning"))
            state.current_agent = "supervisor"
            return state
            
        tool_results = []
        for tool in self.sast_tools:
            try:
                result = tool.invoke({"target_path": "temp_scan_target"})
                tool_results.append(str(result))
            except Exception as e:
                logger.exception("SAST tool execution failed")

        system_prompt = registry.get(PromptType.SWARM_SECOPS)
        human_msg = f"Code:\n{code_to_review}\n\nSAST Results:\n{tool_results}"
        
        try:
            structured_llm = self.llm.with_structured_output(SecOpsEvaluation)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            eval_result = await structured_llm.ainvoke(messages)
            
            scan_results = f"MODULE SECOPS: Security evaluation completed. Secure: {eval_result.is_secure}. Details: {eval_result.vulnerability_summary}"
            state.messages.append(AIMessage(content=scan_results))
            state.artifacts["security_report"] = scan_results
            logger.info("SecOps LLM evaluation completed successfully")
        except Exception as e:
            logger.exception("SecOps LLM evaluation failed")
            state.messages.append(AIMessage(content="MODULE SECOPS: LLM evaluation failed"))
            
        state.current_agent = "supervisor"
        return state
