import re
from difflib import SequenceMatcher

from src.core.common import plain_text


def requirement_finding(rule_id, severity, message, suggestion, target_field, **values):
    return {
        "rule_id": rule_id,
        "severity": severity,
        "span": None,
        "message": message,
        "suggestion": suggestion,
        "target_field": target_field,
        **values,
    }


def requirement_findings(version, acceptance_criteria=None):
    text = version.get("plain_text_projection") or plain_text(version.get("content_doc", {}))
    findings = []
    if not text.strip():
        findings.append(
            requirement_finding(
                "MISSING_REQUIREMENT_CONTENT",
                "error",
                "Nội dung yêu cầu đang để trống",
                "Nhập mô tả phạm vi hoặc chức năng mà hệ thống phải đáp ứng",
                "content",
            )
        )
    if not any(str(item).strip() for item in version.get("actors", [])):
        findings.append(
            requirement_finding(
                "MISSING_ACTOR",
                "error",
                "Yêu cầu chưa xác định tác nhân",
                "Bổ sung tác nhân thực hiện hoặc chịu tác động",
                "actors",
            )
        )
    if not any(str(item).strip() for item in version.get("business_rules", [])):
        findings.append(
            requirement_finding(
                "MISSING_BUSINESS_RULE",
                "error",
                "Yêu cầu chưa có quy tắc nghiệp vụ",
                "Bổ sung quy tắc có căn cứ hoặc xác nhận rõ yêu cầu không có quy tắc nghiệp vụ",
                "business_rules",
            )
        )
    criteria = []
    for index, item in enumerate(acceptance_criteria or []):
        content = (
            str(item.get("plain_text") or plain_text(item.get("content_doc", {})) or "")
            if isinstance(item, dict)
            else str(item or "")
        ).strip()
        criteria.append(
            {
                "id": item.get("_id") if isinstance(item, dict) else None,
                "key": item.get("key") if isinstance(item, dict) else f"AC-{index + 1:02d}",
                "text": content,
            }
        )
    criteria_text = "\n".join(item["text"] for item in criteria).strip()
    has_criteria = (
        bool(criteria_text)
        if acceptance_criteria is not None
        else bool(version.get("acceptance_criterion_ids"))
    )
    if not has_criteria:
        findings.append(
            requirement_finding(
                "MISSING_ACCEPTANCE_CRITERIA",
                "error",
                "Yêu cầu chưa có tiêu chí chấp nhận",
                "Bổ sung ít nhất một điều kiện chấp nhận có thể kiểm thử",
                "acceptance_criteria",
            )
        )
    for criterion in criteria:
        identity = {"criterion_id": criterion["id"], "criterion_key": criterion["key"]}
        if not criterion["text"]:
            findings.append(
                requirement_finding(
                    "EMPTY_ACCEPTANCE_CRITERION",
                    "error",
                    f"Tiêu chí {criterion['key']} đang để trống",
                    "Nhập điều kiện kích hoạt và hành vi quan sát được",
                    "acceptance_criteria",
                    **identity,
                )
            )
            continue
    return findings


def requirement_duplicate_score(left, right):
    left_text = _requirement_projection(left)
    right_text = _requirement_projection(right)
    if not left_text or not right_text:
        return 0, []
    if left_text == right_text:
        return 1, ["Nội dung yêu cầu trùng khớp hoàn toàn"]
    lexical = SequenceMatcher(None, left_text, right_text).ratio()
    left_terms = set(re.findall(r"[\wÀ-ỹ]+", left_text))
    right_terms = set(re.findall(r"[\wÀ-ỹ]+", right_text))
    semantic = len(left_terms & right_terms) / max(1, len(left_terms | right_terms))
    left_rules = {
        str(value).strip().lower() for value in left.get("business_rules", []) if str(value).strip()
    }
    right_rules = {
        str(value).strip().lower()
        for value in right.get("business_rules", [])
        if str(value).strip()
    }
    rule_overlap = (
        len(left_rules & right_rules) / max(1, len(left_rules | right_rules))
        if left_rules or right_rules
        else 0
    )
    score = min(1, 0.65 * lexical + 0.25 * semantic + 0.1 * rule_overlap)
    reasons = []
    if lexical >= 0.75:
        reasons.append("Tiêu đề và nội dung gần giống")
    if semantic >= 0.55:
        reasons.append("Có nhiều thuật ngữ nghiệp vụ chung")
    if rule_overlap > 0:
        reasons.append("Có quy tắc nghiệp vụ trùng nhau")
    return round(score, 4), reasons


def lint_test_case(draft):
    findings = []
    expected = plain_text(draft.get("expected_result_doc", {}))
    precondition = plain_text(draft.get("preconditions_doc", {}))
    if not expected:
        findings.append(_finding("TCQ-001", "error", "Thiếu kết quả mong đợi"))
    if not precondition:
        findings.append(_finding("TCQ-002", "warning", "Thiếu điều kiện tiên quyết"))
    if not draft.get("requirement_version_ids") and not draft.get("acceptance_criterion_ids"):
        findings.append(_finding("TCQ-005", "error", "Ca kiểm thử chưa có liên kết truy vết"))
    if not draft.get("test_data") and not any(
        step.get("test_data") for step in draft.get("steps", [])
    ):
        findings.append(_finding("TCQ-009", "warning", "Thiếu dữ liệu kiểm thử"))
    for step in draft.get("steps", []):
        if not plain_text(step.get("expected_doc", {})):
            findings.append(
                {
                    **_finding("TCQ-001", "warning", "Bước chưa có kết quả mong đợi"),
                    "step_id": step.get("id"),
                }
            )
    return findings


def duplicate_score(left, right):
    left_text = _test_projection(left)
    right_text = _test_projection(right)
    lexical = SequenceMatcher(None, left_text, right_text).ratio()
    left_links = set(left.get("requirement_version_ids", [])) | set(
        left.get("acceptance_criterion_ids", [])
    )
    right_links = set(right.get("requirement_version_ids", [])) | set(
        right.get("acceptance_criterion_ids", [])
    )
    trace = len(left_links & right_links) / max(1, len(left_links | right_links))
    left_steps = len(left.get("steps", []))
    right_steps = len(right.get("steps", []))
    structure = 1 - abs(left_steps - right_steps) / max(1, left_steps, right_steps)
    score = 0.6 * lexical + 0.25 * trace + 0.15 * structure
    reasons = []
    if lexical >= 0.75:
        reasons.append("Nội dung và kết quả mong đợi gần giống")
    if trace > 0:
        reasons.append("Cùng liên kết yêu cầu hoặc tiêu chí chấp nhận")
    if structure >= 0.8:
        reasons.append("Cấu trúc bước tương đồng")
    return round(score, 4), reasons


def _test_projection(value):
    step_text = " ".join(
        f"{plain_text(step.get('action_doc', {}))} {plain_text(step.get('expected_doc', {}))}"
        for step in value.get("steps", [])
    )
    return " ".join(
        [
            str(value.get("title", "")),
            plain_text(value.get("preconditions_doc", {})),
            step_text,
            plain_text(value.get("expected_result_doc", {})),
        ]
    ).lower()


def _requirement_projection(value):
    title = str(value.get("title", ""))
    content = value.get("plain_text_projection") or plain_text(value.get("content_doc", {}))
    criteria = " ".join(
        item.get("plain_text") or plain_text(item.get("content_doc", {}))
        for item in value.get("acceptance_criteria", [])
    )
    return " ".join(f"{title} {content} {criteria}".lower().split())


def _finding(rule_id, severity, message):
    return {
        "rule_id": rule_id,
        "severity": severity,
        "span": None,
        "message": message,
        "suggestion": "Cập nhật bản nháp rồi chạy kiểm tra lại",
    }
