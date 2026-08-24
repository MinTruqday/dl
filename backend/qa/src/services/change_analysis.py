import re
from difflib import SequenceMatcher


def semantic_changes(before, after):
    before_text = before.get("plain_text_projection", "")
    after_text = after.get("plain_text_projection", "")
    if before_text.strip() == after_text.strip():
        return []
    before_numbers = [int(value) for value in re.findall(r"\b\d+\b", before_text)]
    after_numbers = [int(value) for value in re.findall(r"\b\d+\b", after_text)]
    changes = []
    if before_numbers != after_numbers:
        changes.append(
            {
                "type": "MODIFIED_BOUNDARY",
                "subject": infer_subject(after_text),
                "before": {"values": before_numbers},
                "after": {"values": after_numbers},
                "confidence": 0.94,
                "evidence": [
                    {"artifact_version_id": before["_id"], "text": before_text[:500]},
                    {"artifact_version_id": after["_id"], "text": after_text[:500]},
                ],
            }
        )
    permission_words = {"quyền", "vai trò", "admin", "tester", "viewer", "permission", "role"}
    if permission_words & set((before_text + " " + after_text).lower().split()):
        changes.append(
            {
                "type": "MODIFIED_PERMISSION",
                "subject": infer_subject(after_text),
                "before": {"text": before_text[:500]},
                "after": {"text": after_text[:500]},
                "confidence": 0.78,
                "evidence": [],
            }
        )
    ratio = SequenceMatcher(None, before_text.lower(), after_text.lower()).ratio()
    if not changes:
        changes.append(
            {
                "type": "TEXT_ONLY" if ratio > 0.9 else "MODIFIED_INPUT",
                "subject": infer_subject(after_text),
                "before": {"text": before_text[:500]},
                "after": {"text": after_text[:500]},
                "confidence": round(max(0.55, 1 - ratio / 2), 4),
                "evidence": [],
            }
        )
    return changes


def classify_test_impact(test_version, changes, direct_trace):
    projection = test_version.get("plain_text_projection", "").lower()
    classifications = []
    reasons = []
    confidence = 0.45
    for change in changes:
        before_values = change.get("before", {}).get("values", [])
        after_values = change.get("after", {}).get("values", [])
        newly_allowed = set(after_values) - set(before_values)
        if change.get("type") == "MODIFIED_BOUNDARY":
            if any(re.search(rf"\b{value}\b", projection) for value in newly_allowed):
                classifications.append("NEEDS_UPDATE")
                reasons.append("Test Case chứa giá trị biên vừa thay đổi")
                confidence = max(confidence, 0.93)
            elif direct_trace:
                classifications.append("STILL_VALID")
                reasons.append("Giá trị kiểm thử không thuộc tập biên mới thay đổi")
                confidence = max(confidence, 0.9)
        elif change.get("type") == "TEXT_ONLY":
            classifications.append("STILL_VALID")
            reasons.append("Thay đổi chỉ ảnh hưởng cách diễn đạt")
            confidence = max(confidence, 0.88)
        elif direct_trace:
            classifications.append("POTENTIALLY_AFFECTED")
            reasons.append("Test Case có liên kết truy vết trực tiếp tới Requirement thay đổi")
            confidence = max(confidence, 0.78)
    if "NEEDS_UPDATE" in classifications:
        classification = "NEEDS_UPDATE"
    elif "POTENTIALLY_AFFECTED" in classifications:
        classification = "POTENTIALLY_AFFECTED"
    elif "STILL_VALID" in classifications:
        classification = "STILL_VALID"
    else:
        classification = "POTENTIALLY_AFFECTED" if direct_trace else "STILL_VALID"
        reasons.append(
            "Có liên kết trực tiếp nhưng chưa đủ bằng chứng cấu trúc"
            if direct_trace
            else "Không tìm thấy bằng chứng Requirement thay đổi tác động Test Case"
        )
    return {
        "test_case_id": test_version["test_case_id"],
        "test_case_version_id": test_version["_id"],
        "test_case_key": test_version.get("test_case_key"),
        "classification": classification,
        "confidence": confidence,
        "reasons": reasons,
        "evidence": [
            {
                "artifact_type": "test_case_version",
                "artifact_version_id": test_version["_id"],
                "direct_trace": direct_trace,
            }
        ],
        "proposed_actions": ["update_expected_result"] if classification == "NEEDS_UPDATE" else [],
    }


def infer_subject(text):
    lowered = text.lower()
    for candidate in ("phone", "password", "email", "permission", "status", "response", "input"):
        if candidate in lowered:
            return candidate
    return "requirement.behavior"
