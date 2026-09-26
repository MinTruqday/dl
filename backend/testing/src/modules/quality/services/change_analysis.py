import re
from difflib import SequenceMatcher

from src.services.domain_policy import domain_policy


def semantic_candidate_score(requirement_text, test_text):
    pattern = domain_policy("text_processing")["token_pattern"]
    requirement_tokens = set(re.findall(pattern, requirement_text.casefold()))
    test_tokens = set(re.findall(pattern, test_text.casefold()))
    if not requirement_tokens or not test_tokens:
        return 0.0
    return len(requirement_tokens & test_tokens) / max(1, len(requirement_tokens))


def semantic_changes(before, after):
    policy = domain_policy("change_analysis")
    before_text = before.get("plain_text_projection", "")
    after_text = after.get("plain_text_projection", "")
    tracked_fields = policy["tracked_fields"]
    changed_fields = [field for field in tracked_fields if before.get(field) != after.get(field)]
    content_changed = before_text.strip() != after_text.strip()
    if not content_changed and not changed_fields:
        return []
    ratio = SequenceMatcher(None, before_text.lower(), after_text.lower()).ratio()
    return [
        {
            "type": policy["modified_input_type"]
            if content_changed
            else policy["text_only_type"],
            "subject": "content" if content_changed else ",".join(changed_fields),
            "before": {
                "text": before_text[: policy["evidence_text_limit"]],
                "fields": {field: before.get(field) for field in changed_fields},
            },
            "after": {
                "text": after_text[: policy["evidence_text_limit"]],
                "fields": {field: after.get(field) for field in changed_fields},
            },
            "confidence": round(
                max(
                    policy["content_confidence_minimum"],
                    1 - ratio / policy["content_confidence_ratio_divisor"],
                ),
                4,
            ),
            "evidence": [
                {
                    "artifact_version_id": before["_id"],
                    "text": before_text[: policy["evidence_text_limit"]],
                },
                {
                    "artifact_version_id": after["_id"],
                    "text": after_text[: policy["evidence_text_limit"]],
                },
            ],
        }
    ]


def classify_test_impact(test_version, changes, direct_trace):
    policy = domain_policy("change_analysis")
    classification = (
        policy["potentially_affected_classification"]
        if direct_trace
        else policy["still_valid_classification"]
    )
    confidence = (
        policy["direct_trace_confidence"]
        if direct_trace
        else policy["indirect_trace_confidence"]
    )
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
