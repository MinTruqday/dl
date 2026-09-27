import re


def normalize_narrative(value):
    text = str(value or "").strip()
    if not text or text in {
        "task_id",
        "status",
        "summary",
        "evidence_refs",
        "reason_codes",
        "proposals",
        "warnings",
        "actions",
        "success_criteria_met",
    }:
        return ""
    if re.search(r"\]\(null\)$", text):
        return ""
    closing = ""
    while text and text[-1] in "\"'”’)":
        closing = text[-1] + closing
        text = text[:-1].rstrip()
    return text.rstrip(".!?… ") + closing


def normalize_narratives(values):
    normalized = [normalize_narrative(value) for value in values]
    return list(dict.fromkeys(value for value in normalized if value))


def normalize_narrative_payload(value, field_name=""):
    if isinstance(value, dict):
        return {
            key: normalize_narrative_payload(item, key) for key, item in value.items()
        }
    if isinstance(value, list):
        if field_name in {
            "answer",
            "summary",
            "title",
            "description",
            "content",
            "message",
            "suggestion",
            "rationale",
            "warning",
            "warnings",
            "executive_summary",
            "risk_explanation",
            "recommendation_narrative",
            "closure_summary",
            "residual_risk_summary",
            "recommendation_rationale",
            "observation",
            "impact",
            "recommendation",
        } and all(isinstance(item, str) for item in value):
            return normalize_narratives(value)
        return [normalize_narrative_payload(item, field_name) for item in value]
    if isinstance(value, str) and field_name in {
        "answer",
        "summary",
        "title",
        "description",
        "content",
        "message",
        "suggestion",
        "rationale",
        "warning",
        "warnings",
        "executive_summary",
        "risk_explanation",
        "recommendation_narrative",
        "closure_summary",
        "residual_risk_summary",
        "recommendation_rationale",
        "observation",
        "impact",
        "recommendation",
    }:
        return normalize_narrative(value)
    return value
