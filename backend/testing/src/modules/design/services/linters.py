import re
from difflib import SequenceMatcher

from src.core.common import plain_text
from src.services.quality_policy import evaluate_rules, quality_policy


def requirement_findings(version, acceptance_criteria=None):
    text = version.get("plain_text_projection") or plain_text(version.get("content_doc", {}))
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
                "key": item.get("key")
                if isinstance(item, dict)
                else f"{quality_policy()['duplicate_scoring']['criterion_key_prefix']}{index + 1:02d}",
                "text": content,
            }
        )
    normalized_version = {
        **version,
        "content": text,
        "acceptance_criteria": [item["text"] for item in criteria]
        if acceptance_criteria is not None
        else version.get("acceptance_criterion_ids", []),
    }
    findings = evaluate_rules("requirement", normalized_version)
    for criterion in criteria:
        identity = {"criterion_id": criterion["id"], "criterion_key": criterion["key"]}
        findings.extend(
            {**finding, **identity}
            for finding in evaluate_rules("acceptance_criterion", criterion)
        )
    return findings


def requirement_duplicate_score(left, right):
    policy = quality_policy()["duplicate_scoring"]
    scoring = policy["requirement"]
    left_text = _requirement_projection(left)
    right_text = _requirement_projection(right)
    if not left_text or not right_text:
        return 0, []
    if left_text == right_text:
        return 1, [scoring["exact_reason"]]
    lexical = SequenceMatcher(None, left_text, right_text).ratio()
    left_terms = set(re.findall(policy["term_pattern"], left_text))
    right_terms = set(re.findall(policy["term_pattern"], right_text))
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
    score = min(
        1,
        scoring["lexical_weight"] * lexical
        + scoring["semantic_weight"] * semantic
        + scoring["rule_weight"] * rule_overlap,
    )
    reasons = []
    if lexical >= scoring["lexical_reason_threshold"]:
        reasons.append(scoring["lexical_reason"])
    if semantic >= scoring["semantic_reason_threshold"]:
        reasons.append(scoring["semantic_reason"])
    if rule_overlap > scoring["rule_reason_threshold"]:
        reasons.append(scoring["rule_reason"])
    return round(score, policy["precision"]), reasons


def lint_test_case(draft):
    findings = evaluate_rules("test_case", draft)
    for step in draft.get("steps", []):
        findings.extend(
            {**finding, "step_id": step.get("id")}
            for finding in evaluate_rules("test_step", step)
        )
    return findings


def duplicate_score(left, right):
    policy = quality_policy()["duplicate_scoring"]
    scoring = policy["test_case"]
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
    score = (
        scoring["lexical_weight"] * lexical
        + scoring["trace_weight"] * trace
        + scoring["structure_weight"] * structure
    )
    reasons = []
    if lexical >= scoring["lexical_reason_threshold"]:
        reasons.append(scoring["lexical_reason"])
    if trace > scoring["trace_reason_threshold"]:
        reasons.append(scoring["trace_reason"])
    if structure >= scoring["structure_reason_threshold"]:
        reasons.append(scoring["structure_reason"])
    return round(score, policy["precision"]), reasons


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
