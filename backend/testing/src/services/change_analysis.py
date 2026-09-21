import re
from difflib import SequenceMatcher


def semantic_candidate_score(requirement_text, test_text):
    requirement_tokens = set(re.findall(r"[\w-]+", requirement_text.casefold()))
    test_tokens = set(re.findall(r"[\w-]+", test_text.casefold()))
    if not requirement_tokens or not test_tokens:
        return 0.0
    return len(requirement_tokens & test_tokens) / max(1, len(requirement_tokens))


def semantic_changes(before, after):
    before_text = before.get("plain_text_projection", "")
    after_text = after.get("plain_text_projection", "")
    tracked_fields = ("title", "actors", "business_rules", "dependencies")
    changed_fields = [field for field in tracked_fields if before.get(field) != after.get(field)]
    content_changed = before_text.strip() != after_text.strip()
    if not content_changed and not changed_fields:
        return []
    ratio = SequenceMatcher(None, before_text.lower(), after_text.lower()).ratio()
    return [
        {
            "type": "MODIFIED_INPUT" if content_changed else "TEXT_ONLY",
            "subject": "content" if content_changed else ",".join(changed_fields),
            "before": {
                "text": before_text[:500],
                "fields": {field: before.get(field) for field in changed_fields},
            },
            "after": {
                "text": after_text[:500],
                "fields": {field: after.get(field) for field in changed_fields},
            },
            "confidence": round(max(0.55, 1 - ratio / 2), 4),
            "evidence": [
                {"artifact_version_id": before["_id"], "text": before_text[:500]},
                {"artifact_version_id": after["_id"], "text": after_text[:500]},
            ],
        }
    ]


def classify_test_impact(test_version, changes, direct_trace):
    classification = "POTENTIALLY_AFFECTED" if direct_trace else "STILL_VALID"
    confidence = 0.78 if direct_trace else 0.45
    reasons = [
        "Có liên kết truy vết trực tiếp tới Requirement thay đổi"
        if direct_trace
        else "Không có liên kết truy vết trực tiếp tới Requirement thay đổi"
    ]
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
        "proposed_actions": [],
    }
