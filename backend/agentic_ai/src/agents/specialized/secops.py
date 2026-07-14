from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from loguru import logger

from src.agents.swarm import SwarmState
from src.core.registry import PromptType, registry
from src.schemas.secops import SecOpsEvaluation
from src.tools.sast import SASTScanner


class SecOpsAgent:
    """
    <module_purpose>
    DocLib SecOps Agent for analyzing generated code using Static Application Security Testing (SAST).
    </module_purpose>
    <contract>
    - Precondition: Valid code to scan.
    - Postcondition: Returns security evaluation and vulnerability summary.
    - Error Handling: Operates standalone or within Swarm; acts as a strict gatekeeper against vulnerabilities.
    </contract>
    """

    def __init__(self, llm):
        self.llm = llm

    async def scan_standalone(self, code: str) -> str:
        sast_output = SASTScanner.full_scan(code)
        system_prompt = registry.get(PromptType.SWARM_SECOPS)
        human_msg = f"Code:\n{code}\n\nSAST Results:\n{sast_output}"
        try:
            structured_llm = self.llm.with_structured_output(SecOpsEvaluation)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            eval_result = await structured_llm.ainvoke(messages)
            return (
                f"Secure: {eval_result.is_secure}\n"
                f"Summary: {eval_result.vulnerability_summary}\n\n"
                f"SAST Output:\n{sast_output}"
            )
        except Exception:
            logger.exception("SecOps standalone LLM evaluation failed")
            return f"LLM evaluation failed. Raw SAST output:\n{sast_output}"

    async def execute(self, state: SwarmState) -> SwarmState:
        logger.info("SecOps execution started via LLM")

        code_to_review = state.artifacts.get("code", "")
        if not code_to_review:
            state.messages.append(AIMessage(content="MODULE SECOPS: Missing code artifact for scanning"))
            state.current_agent = "supervisor"
            return state

        sast_output = SASTScanner.full_scan(code_to_review)

        system_prompt = registry.get(PromptType.SWARM_SECOPS)
        human_msg = f"Code:\n{code_to_review}\n\nSAST Results:\n{sast_output}"

        try:
            structured_llm = self.llm.with_structured_output(SecOpsEvaluation)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            eval_result = await structured_llm.ainvoke(messages)

            scan_results = (
                f"MODULE SECOPS: Security evaluation completed. "
                f"Secure: {eval_result.is_secure}. "
                f"Details: {eval_result.vulnerability_summary}\n\n"
                f"SAST Output:\n{sast_output}"
            )
            state.messages.append(AIMessage(content=scan_results))
            state.artifacts["security_report"] = scan_results
            logger.info("SecOps LLM evaluation completed successfully")
        except Exception:
            logger.exception("SecOps LLM evaluation failed")
            state.messages.append(AIMessage(content=f"MODULE SECOPS: LLM evaluation failed. SAST raw output:\n{sast_output}"))
            state.artifacts["security_report"] = f"Raw SAST output:\n{sast_output}"

        state.current_agent = "supervisor"
        return state
