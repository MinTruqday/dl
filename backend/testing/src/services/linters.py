import re
from difflib import SequenceMatcher

from src.core.common import plain_text


AMBIGUOUS_TERMS = ("nhanh", "dễ dùng", "hợp lý", "tối ưu", "kịp thời", "bảo mật tốt")
NON_DETERMINISTIC = ("thích hợp", "đầy đủ", "chính xác", "ổn định", "thân thiện")


def requirement_findings(version):
    text = version.get("plain_text_projection") or plain_text(version.get("content_doc", {}))
    lowered = text.lower()
    findings = []
    for term in AMBIGUOUS_TERMS:
        start = lowered.find(term)
        if start >= 0:
            findings.append(
                {
                    "rule_id": "AMBIGUOUS_TERM",
                    "severity": "warning",
                    "span": {"start": start, "end": start + len(term), "text": text[start : start + len(term)]},
                    "message": f"Thuật ngữ {term} chưa có tiêu chí đo lường",
                    "suggestion": "Thay bằng ngưỡng hoặc hành vi có thể kiểm thử",
                }
            )
    if not version.get("actors"):
        findings.append(
            {
                "rule_id": "MISSING_ACTOR",
                "severity": "warning",
                "span": None,
                "message": "Requirement chưa xác định actor",
                "suggestion": "Bổ sung actor thực hiện hoặc chịu tác động",
            }
        )
    if not version.get("acceptance_criterion_ids"):
        findings.append(
            {
                "rule_id": "MISSING_ACCEPTANCE_CRITERIA",
                "severity": "error",
                "span": None,
                "message": "Requirement chưa có Acceptance Criterion",
                "suggestion": "Bổ sung ít nhất một điều kiện chấp nhận có thể kiểm thử",
            }
        )
    if not re.search(r"(khi|nếu|given|when|trong trường hợp)", lowered):
        findings.append(
            {
                "rule_id": "MISSING_CONDITION",
                "severity": "warning",
                "span": None,
                "message": "Chưa nhận diện được điều kiện kích hoạt",
                "suggestion": "Nêu rõ điều kiện hoặc trạng thái trước hành vi",
            }
        )
    if not re.search(r"(thì|then|phải|hiển thị|trả về|cho phép|từ chối)", lowered):
        findings.append(
            {
                "rule_id": "MISSING_EXPECTED_BEHAVIOR",
                "severity": "error",
                "span": None,
                "message": "Chưa nhận diện được hành vi mong đợi",
                "suggestion": "Mô tả kết quả quan sát được của hệ thống",
            }
        )
    return findings


def requirement_duplicate_score(left, right):
    left_text = _requirement_projection(left)
    right_text = _requirement_projection(right)
    if not left_text or not right_text:
        return 0, []
    if left_text == right_text:
        return 1, ["Nội dung Requirement trùng khớp hoàn toàn"]
    lexical = SequenceMatcher(None, left_text, right_text).ratio()
    left_terms = set(re.findall(r"[\wÀ-ỹ]+", left_text))
    right_terms = set(re.findall(r"[\wÀ-ỹ]+", right_text))
    semantic = len(left_terms & right_terms) / max(1, len(left_terms | right_terms))
    left_rules = {
        str(value).strip().lower()
        for value in left.get("business_rules", [])
        if str(value).strip()
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
        findings.append(_finding("TCQ-005", "error", "Test Case chưa có liên kết truy vết"))
    if not draft.get("test_data") and not any(step.get("test_data") for step in draft.get("steps", [])):
        findings.append(_finding("TCQ-009", "warning", "Thiếu dữ liệu kiểm thử"))
    for step in draft.get("steps", []):
        action = plain_text(step.get("action_doc", {}))
        if len(re.findall(r"\b(và|sau đó|then|and)\b", action.lower())) >= 2:
            findings.append(
                {
                    **_finding("TCQ-003", "warning", "Một bước đang chứa nhiều hành động"),
                    "step_id": step.get("id"),
                }
            )
        if not plain_text(step.get("expected_doc", {})):
            findings.append(
                {
                    **_finding("TCQ-001", "warning", "Bước chưa có kết quả mong đợi"),
                    "step_id": step.get("id"),
                }
            )
    lowered = expected.lower()
    if any(term in lowered for term in AMBIGUOUS_TERMS + NON_DETERMINISTIC):
        findings.append(_finding("TCQ-004", "warning", "Kết quả mong đợi còn mơ hồ"))
    return findings


def duplicate_score(left, right):
    left_text = _test_projection(left)
    right_text = _test_projection(right)
    lexical = SequenceMatcher(None, left_text, right_text).ratio()
    left_links = set(left.get("requirement_version_ids", [])) | set(left.get("acceptance_criterion_ids", []))
    right_links = set(right.get("requirement_version_ids", [])) | set(right.get("acceptance_criterion_ids", []))
    trace = len(left_links & right_links) / max(1, len(left_links | right_links))
    left_steps = len(left.get("steps", []))
    right_steps = len(right.get("steps", []))
    structure = 1 - abs(left_steps - right_steps) / max(1, left_steps, right_steps)
    score = 0.6 * lexical + 0.25 * trace + 0.15 * structure
    reasons = []
    if lexical >= 0.75:
        reasons.append("Nội dung và kết quả mong đợi gần giống")
    if trace > 0:
        reasons.append("Cùng liên kết Requirement hoặc Acceptance Criterion")
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
