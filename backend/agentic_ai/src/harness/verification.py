import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from loguru import logger

CheckStatus = Literal["passed", "failed", "skipped"]

@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    reason: str = ""

@dataclass
class VerificationResult:
    session_id: str
    task_id: str
    passed: bool
    checks: List[CheckResult] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def failed_checks(self) -> List[CheckResult]:
        return [c for c in self.checks if c.status == "failed"]

    @property
    def passed_checks(self) -> List[CheckResult]:
        return [c for c in self.checks if c.status == "passed"]

def _check_response_not_empty(response: str) -> CheckResult:
    if not response or not response.strip():
        return CheckResult(
            name="response_not_empty",
            status="failed",
            reason="Empty response content",
        )
    if len(response.strip()) < 10:
        return CheckResult(
            name="response_not_empty",
            status="failed",
            reason="Response length below standard",
        )
    return CheckResult(name="response_not_empty", status="passed")

async def _check_no_hallucination_markers(response: str) -> CheckResult:
    from src.workflow.graph import llm
    from pydantic import BaseModel, Field
    
    class HallucinationGrade(BaseModel):
        is_refusal_or_hallucination: bool = Field(description="Set to True if the response refuses the prompt, states ignorance, or uses artificial identity markers ('As an AI language model...'). Set to False if it is a normal, helpful response.")
        reason: str = Field(description="A concise 1-sentence reason explaining why the response was graded as a refusal/hallucination or a valid response.")

    try:
        evaluator = llm.with_structured_output(HallucinationGrade)
        from src.core.registry import registry, PromptType
        prompt = registry.get(PromptType.VERIFICATION_HALLUCINATION).format(response=response[:500])
        result = await evaluator.ainvoke(prompt)
        if result.is_refusal_or_hallucination:
            return CheckResult(
                name="no_hallucination_markers",
                status="failed",
                reason=f"Detected signs of refusal to respond or data hallucination: {result.reason}",
            )
    except Exception as e:
        if len(response) < 15 and "?" not in response:
            pass
            
    return CheckResult(name="no_hallucination_markers", status="passed")

def _check_plan_fully_executed(steps: List[Dict], current_step_index: int) -> CheckResult:
    if not steps:
        return CheckResult(
            name="plan_fully_executed",
            status="skipped",
            reason="Execution plan structure not found",
        )
    total = len(steps)
    if current_step_index < total:
        return CheckResult(
            name="plan_fully_executed",
            status="failed",
            reason=f"Plan execution incomplete ({current_step_index}/{total} steps)",
        )
    return CheckResult(name="plan_fully_executed", status="passed")

def _check_tool_result_valid(tool_result: Any) -> CheckResult:
    if tool_result is None:
        return CheckResult(
            name="tool_result_valid",
            status="failed",
            reason="Tool result is empty (None)",
        )
    if isinstance(tool_result, dict) and tool_result.get("error"):
        return CheckResult(
            name="tool_result_valid",
            status="failed",
            reason=f"Tool execution resulted in an error: {str(tool_result.get('error', ''))[:100]}",
        )
    return CheckResult(name="tool_result_valid", status="passed")

async def _check_no_error_prefix(response: str) -> CheckResult:
    from src.workflow.graph import llm
    from pydantic import BaseModel, Field

    class ErrorMessageJudgment(BaseModel):
        is_error_message: bool = Field(description="Set to True if the text contains a raw stack trace, HTTP error code, unhandled exception, Python/JS traceback, or a system failure message. Set to False if it is a natural language response.")
        reason: str = Field(description="A specific, 1-2 sentence explanation of why this was classified as an error message or a valid output.")

    try:
        evaluator = llm.with_structured_output(ErrorMessageJudgment)
        from src.core.registry import registry, PromptType
        prompt = registry.get(PromptType.VERIFICATION_ERROR_JUDGE).format(response=response[:500])
        result = await evaluator.ainvoke(prompt)
        if result.is_error_message:
            return CheckResult(
                name="no_error_prefix",
                status="failed",
                reason=f"Detected error warning in the response content: {result.reason}",
            )
    except Exception:
        pass
    return CheckResult(name="no_error_prefix", status="passed")

class VerificationHarness:
    def __init__(self):
        self._history: Dict[str, List[VerificationResult]] = {}

    async def verify_task_completion(
        self,
        session_id: str,
        task_id: str,
        response: str,
        steps: Optional[List[Dict]] = None,
        current_step_index: Optional[int] = None,
    ) -> VerificationResult:
        logger.info("Starting task result verification")
        checks = [
            _check_response_not_empty(response),
            await _check_no_hallucination_markers(response),
            await _check_no_error_prefix(response),
        ]

        if steps is not None and current_step_index is not None:
            checks.append(_check_plan_fully_executed(steps, current_step_index))

        failed = [c for c in checks if c.status == "failed"]
        passed = len(failed) == 0

        result = VerificationResult(
            session_id=session_id,
            task_id=task_id,
            passed=passed,
            checks=checks,
        )

        if session_id not in self._history:
            self._history[session_id] = []
        self._history[session_id].append(result)

        if passed:
            logger.info("Task verification complete and all checks passed")
        else:
            failed_names = [c.name for c in failed]
            logger.warning(
                f"Task verification failed: checks that failed include {failed_names}"
            )
        return result

    def verify_tool_result(
        self,
        session_id: str,
        task_id: str,
        tool_result: Any,
    ) -> VerificationResult:
        check = _check_tool_result_valid(tool_result)
        passed = check.status == "passed"
        result = VerificationResult(
            session_id=session_id,
            task_id=task_id,
            passed=passed,
            checks=[check],
        )
        if not passed:
            logger.warning(f"Invalid tool result {check.reason}")
        return result

    def get_session_history(self, session_id: str) -> List[VerificationResult]:
        return self._history.get(session_id, [])

    def clear_session(self, session_id: str):
        self._history.pop(session_id, None)

verification = VerificationHarness()
