from typing import Any


def classify_evidence(response: dict[str, Any]):
    flags = set(response.get("technical_flags", []))
    if response.get("score_status", "final") != "final":
        return "exclude"
    if "duplicate" in flags or "invalid" in flags or "leaked" in flags:
        return "exclude"
    if not response.get("is_first_exposure", True):
        return "exclude"
    if response.get("explanation_seen_before_answer"):
        return "exclude"
    if response.get("hint_used"):
        return "down_weight"
    if response.get("delivery_context") == "practice":
        return "review"
    if "timeout" in flags or "network_error" in flags or "abnormal_time" in flags:
        return "review"
    return "eligible"


def eligible_responses(responses: list[dict[str, Any]]):
    return [response for response in responses if classify_evidence(response) == "eligible"]
