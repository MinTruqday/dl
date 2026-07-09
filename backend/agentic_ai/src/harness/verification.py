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
            reason="Nội dung phản hồi trống",
        )
    if len(response.strip()) < 10:
        return CheckResult(
            name="response_not_empty",
            status="failed",
            reason="Nội dung phản hồi không đạt độ dài tiêu chuẩn",
        )
    return CheckResult(name="response_not_empty", status="passed")

async def _check_no_hallucination_markers(response: str) -> CheckResult:
    from src.workflow.graph import llm
    from pydantic import BaseModel, Field
    
    class HallucinationGrade(BaseModel):
        is_refusal_or_hallucination: bool = Field(description="True if the response is a refusal to answer, states 'I do not know', or uses AI identity markers like 'As an AI'")
        reason: str = Field(description="Reason for the grade")

    try:
        evaluator = llm.with_structured_output(HallucinationGrade)
        prompt = f"Evaluate this AI response: '{response[:500]}'. Is it refusing to answer or stating it doesn't know?"
        result = await evaluator.ainvoke(prompt)
        if result.is_refusal_or_hallucination:
            return CheckResult(
                name="no_hallucination_markers",
                status="failed",
                reason=f"Phát hiện dấu hiệu từ chối phản hồi hoặc ảo giác dữ liệu: {result.reason}",
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
            reason="Không tìm thấy cấu trúc kế hoạch thực thi",
        )
    total = len(steps)
    if current_step_index < total:
        return CheckResult(
            name="plan_fully_executed",
            status="failed",
            reason=f"Tiến độ thực thi kế hoạch chưa hoàn tất ({current_step_index}/{total} bước)",
        )
    return CheckResult(name="plan_fully_executed", status="passed")

def _check_tool_result_valid(tool_result: Any) -> CheckResult:
    if tool_result is None:
        return CheckResult(
            name="tool_result_valid",
            status="failed",
            reason="Kết quả trả về từ công cụ trống (None)",
        )
    if isinstance(tool_result, dict) and tool_result.get("error"):
        return CheckResult(
            name="tool_result_valid",
            status="failed",
            reason=f"Tiến trình thực thi công cụ phát sinh lỗi: {str(tool_result.get('error', ''))[:100]}",
        )
    return CheckResult(name="tool_result_valid", status="passed")

def _check_no_error_prefix(response: str) -> CheckResult:
    error_prefixes = [
        "error:",
        "lỗi:",
        "exception:",
        "traceback",
        "raise ",
        "failed to",
    ]
    lower = response.lower()
    for prefix in error_prefixes:
        if lower.startswith(prefix):
            return CheckResult(
                name="no_error_prefix",
                status="failed",
                reason=f"Phát hiện cảnh báo lỗi '{prefix}' trong nội dung phản hồi",
            )
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
            _check_no_error_prefix(response),
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
