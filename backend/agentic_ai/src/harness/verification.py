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
            reason="Phản hồi trống rỗng không chứa nội dung có ý nghĩa",
        )
    if len(response.strip()) < 10:
        return CheckResult(
            name="response_not_empty",
            status="failed",
            reason="Phản hồi quá ngắn để được coi là hợp lệ",
        )
    return CheckResult(name="response_not_empty", status="passed")

def _check_no_hallucination_markers(response: str) -> CheckResult:
    hallucination_signals = [
        "i don't know",
        "i cannot",
        "i am unable",
        "as an ai",
        "i'm just an ai",
        "tôi không biết",
        "tôi không thể",
        "tôi không có khả năng",
        "[thông tin không có sẵn]",
        "[không tìm thấy]",
        "undefined",
        "null",
        "none found",
    ]
    response_lower = response.lower()
    for signal in hallucination_signals:
        if signal in response_lower:
            return CheckResult(
                name="no_hallucination_markers",
                status="failed",
                reason=f"Phát hiện tín hiệu hallucination: '{signal}'",
            )
    return CheckResult(name="no_hallucination_markers", status="passed")

def _check_plan_fully_executed(steps: List[Dict], current_step_index: int) -> CheckResult:
    if not steps:
        return CheckResult(
            name="plan_fully_executed",
            status="skipped",
            reason="Không có kế hoạch thực thi để kiểm tra",
        )
    total = len(steps)
    if current_step_index < total:
        return CheckResult(
            name="plan_fully_executed",
            status="failed",
            reason=f"Kế hoạch chưa hoàn thành: đã thực hiện {current_step_index}/{total} bước",
        )
    return CheckResult(name="plan_fully_executed", status="passed")

def _check_tool_result_valid(tool_result: Any) -> CheckResult:
    if tool_result is None:
        return CheckResult(
            name="tool_result_valid",
            status="failed",
            reason="Kết quả tool trả về None",
        )
    if isinstance(tool_result, dict) and tool_result.get("error"):
        return CheckResult(
            name="tool_result_valid",
            status="failed",
            reason=f"Tool trả về lỗi: {str(tool_result.get('error', ''))[:100]}",
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
                reason=f"Phản hồi bắt đầu bằng tín hiệu lỗi: '{prefix}'",
            )
    return CheckResult(name="no_error_prefix", status="passed")

class VerificationHarness:
    def __init__(self):
        self._history: Dict[str, List[VerificationResult]] = {}

    def verify_task_completion(
        self,
        session_id: str,
        task_id: str,
        response: str,
        steps: Optional[List[Dict]] = None,
        current_step_index: Optional[int] = None,
    ) -> VerificationResult:
        logger.info("Bắt đầu xác minh kết quả tác vụ")
        checks = [
            _check_response_not_empty(response),
            _check_no_hallucination_markers(response),
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
            logger.info("Xác minh tác vụ hoàn tất: tất cả kiểm tra đều đạt")
        else:
            failed_names = [c.name for c in failed]
            logger.warning(
                f"Xác minh tác vụ thất bại: các kiểm tra không đạt gồm {failed_names}"
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
            logger.warning(f"Kết quả tool không hợp lệ: {check.reason}")
        return result

    def get_session_history(self, session_id: str) -> List[VerificationResult]:
        return self._history.get(session_id, [])

    def clear_session(self, session_id: str):
        self._history.pop(session_id, None)

verification = VerificationHarness()
