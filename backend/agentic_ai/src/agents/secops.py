import json
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

    async def _invoke_slm(self, messages) -> SecOpsEvaluation:
        try:
            structured_llm = self.llm.with_structured_output(SecOpsEvaluation)
            return await structured_llm.ainvoke(messages)
        except Exception as e:
            logger.exception("SLM execution error")
            raise e

    async def _assess_dependency_vulnerabilities(self, code: str) -> str:
        import re
        
        imports = re.findall(r"^(?:import|from)\s+([a-zA-Z0-9_]+)", code, re.MULTILINE)
        if not imports:
            return json.dumps({"status": "not_applicable", "packages": []})

        return json.dumps(
            {
                "status": "not_assessed",
                "reason_code": "dependency_versions_unavailable",
                "packages": sorted(set(imports)),
            }
        )

    async def scan_standalone(self, code: str) -> str:
        sast_output = await SASTScanner.full_scan(code)
        dependency_output = await self._assess_dependency_vulnerabilities(code)
        system_prompt = registry.get(PromptType.SWARM_SECOPS)
        human_msg = json.dumps(
            {
                "code": code,
                "sast": json.loads(sast_output),
                "dependencies": json.loads(dependency_output),
            },
            ensure_ascii=False,
        )
        try:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            eval_result = await self._invoke_slm(messages)
            return json.dumps(
                {
                    "status": "success",
                    "is_secure": eval_result.is_secure,
                    "summary": eval_result.vulnerability_summary,
                    "sast": json.loads(sast_output),
                    "dependencies": json.loads(dependency_output),
                },
                ensure_ascii=False,
            )
        except Exception:
            logger.exception("SecOps standalone LLM evaluation failed")
            return json.dumps(
                {
                    "status": "model_evaluation_failed",
                    "sast": json.loads(sast_output),
                    "dependencies": json.loads(dependency_output),
                },
                ensure_ascii=False,
            )

    async def execute(self, state: SwarmState) -> SwarmState:
        logger.info("SecOps execution started via LLM")

        code_to_review = state.artifacts.get("code", "")
        if not code_to_review:
            state.messages.append(AIMessage(content=json.dumps({"status": "code_artifact_missing"})))
            state.current_agent = "supervisor"
            return state

        sast_output = await SASTScanner.full_scan(code_to_review)
        dependency_output = await self._assess_dependency_vulnerabilities(code_to_review)

        system_prompt = registry.get(PromptType.SWARM_SECOPS)
        human_msg = json.dumps(
            {
                "code": code_to_review,
                "sast": json.loads(sast_output),
                "dependencies": json.loads(dependency_output),
            },
            ensure_ascii=False,
        )

        try:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            eval_result = await self._invoke_slm(messages)

            scan_results = json.dumps(
                {
                    "status": "success",
                    "is_secure": eval_result.is_secure,
                    "summary": eval_result.vulnerability_summary,
                    "sast": json.loads(sast_output),
                    "dependencies": json.loads(dependency_output),
                },
                ensure_ascii=False,
            )
            state.messages.append(AIMessage(content=scan_results))
            state.artifacts["security_report"] = scan_results
            state.artifacts["security_approved"] = eval_result.is_secure
            logger.info("SecOps LLM evaluation completed")
        except Exception:
            logger.exception("SecOps LLM evaluation failed")
            scan_results = json.dumps(
                {
                    "status": "model_evaluation_failed",
                    "sast": json.loads(sast_output),
                    "dependencies": json.loads(dependency_output),
                },
                ensure_ascii=False,
            )
            state.messages.append(AIMessage(content=scan_results))
            state.artifacts["security_report"] = scan_results
            state.artifacts["security_approved"] = False

        state.current_agent = "supervisor"
        return state
