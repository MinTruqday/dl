from src.core.common import plain_text


def evaluate_rules(scope, value):
    if scope == "requirement":
        return [
            finding
            for finding in (
                _finding("MISSING_REQUIREMENT_CONTENT", "error", "Nội dung yêu cầu đang để trống", "Nhập mô tả phạm vi hoặc chức năng mà hệ thống phải đáp ứng", "content") if not _text(value.get("content")) else None,
                _finding("MISSING_ACTOR", "error", "Yêu cầu chưa xác định tác nhân", "Bổ sung tác nhân thực hiện hoặc chịu tác động", "actors") if not _values(value.get("actors")) else None,
                _finding("MISSING_BUSINESS_RULE", "error", "Yêu cầu chưa có quy tắc nghiệp vụ", "Bổ sung quy tắc có căn cứ hoặc xác nhận rõ yêu cầu không có quy tắc nghiệp vụ", "business_rules") if not _values(value.get("business_rules")) else None,
                _finding("MISSING_ACCEPTANCE_CRITERIA", "error", "Yêu cầu chưa có tiêu chí chấp nhận", "Bổ sung ít nhất một điều kiện chấp nhận có thể kiểm thử", "acceptance_criteria") if not _values(value.get("acceptance_criteria")) else None,
            )
            if finding
        ]
    if scope == "acceptance_criterion" and not _text(value.get("text")):
        return [_finding("EMPTY_ACCEPTANCE_CRITERION", "error", f"Tiêu chí {value.get('key') or ''} đang để trống", "Nhập điều kiện kích hoạt và hành vi quan sát được", "acceptance_criteria")]
    if scope == "test_case":
        findings = []
        if not _text(value.get("expected_result_doc")):
            findings.append(_finding("TCQ-001", "error", "Thiếu kết quả mong đợi", "Cập nhật kết quả mong đợi rồi chạy kiểm tra lại"))
        if not _text(value.get("preconditions_doc")):
            findings.append(_finding("TCQ-002", "warning", "Thiếu điều kiện tiên quyết", "Cập nhật điều kiện tiên quyết rồi chạy kiểm tra lại"))
        if not _values(value.get("requirement_version_ids")) and not _values(value.get("acceptance_criterion_ids")):
            findings.append(_finding("TCQ-005", "error", "Ca kiểm thử chưa có liên kết truy vết", "Liên kết yêu cầu hoặc tiêu chí chấp nhận rồi chạy kiểm tra lại"))
        if not _values(value.get("test_data")) and not any(_values(item.get("test_data")) for item in value.get("steps", [])):
            findings.append(_finding("TCQ-009", "warning", "Thiếu dữ liệu kiểm thử", "Bổ sung dữ liệu kiểm thử cho ca hoặc từng bước"))
        return findings
    if scope == "test_step" and not _text(value.get("expected_doc")):
        return [_finding("TCQ-001", "warning", "Bước chưa có kết quả mong đợi", "Bổ sung kết quả mong đợi cho bước")]
    if scope == "test_basis" and not _text(value.get("text")):
        return [{**_finding("EMPTY_EXPECTED_BEHAVIOR", "BLOCKER", "Nội dung kiểm thử đang trống", "Bổ sung tiêu chí quan sát được và có thể kiểm chứng"), "category": "UNTESTABLE"}]
    return []


def _finding(rule_id, severity, message, suggestion, target_field=None):
    finding = {"rule_id": rule_id, "severity": severity, "span": None, "message": message, "suggestion": suggestion}
    if target_field:
        finding["target_field"] = target_field
    return finding


def _text(value):
    return plain_text(value).strip() if isinstance(value, dict) else str(value or "").strip()


def _values(value):
    values = value if isinstance(value, list) else [value]
    return [item for item in values if _text(item)]
