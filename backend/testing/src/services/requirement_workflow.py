import hashlib
import json

from src.core.common import plain_text
from src.services.domain_policy import domain_policy


WORKFLOW_POLICY = domain_policy("requirement_workflow")


def text_doc(value):
    return {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": str(value)}]}],
    }


def serialized_content(content):
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def acceptance_criterion_text(item):
    return str(item.get("plain_text") or plain_text(item.get("content_doc", {})) or "").strip()


def normalized_business_rule_lines(values):
    normalized = []
    for index, value in enumerate(values or [], 1):
        text = str(value).strip()
        if not text:
            continue
        prefix, separator, remainder = text.partition(":")
        identity = prefix.upper()
        prefix_length = len(WORKFLOW_POLICY["business_rule_prefix"])
        if (
            separator
            and identity.startswith(WORKFLOW_POLICY["business_rule_prefix"])
            and identity[prefix_length:].isdigit()
        ):
            normalized.append(f"{identity}: {remainder.strip()}")
        else:
            normalized.append(f"{WORKFLOW_POLICY['business_rule_prefix']}{index:02d}: {text}")
    return normalized


def prepare_requirement_ai_suggestion(candidate, acceptance_criteria):
    suggestion = dict(candidate)
    patch = {}
    mappings = WORKFLOW_POLICY["revised_field_mappings"]
    for source, target in mappings.items():
        if suggestion.get(source) is not None:
            patch[target] = (
                normalized_business_rule_lines(suggestion[source])
                if source == "revised_business_rules"
                else suggestion[source]
            )
    if suggestion.get("revised_acceptance_criteria") is not None:
        existing = {item.get("key"): item for item in acceptance_criteria}
        patch["acceptance_criteria"] = [
            {
                "key": item["key"],
                "content_doc": text_doc(item["content"]),
                "status": existing.get(item["key"], {}).get(
                    "status", WORKFLOW_POLICY["default_criterion_status"]
                ),
                "source_span": existing.get(item["key"], {}).get("source_span"),
            }
            for item in suggestion["revised_acceptance_criteria"]
        ]
    suggestion["patch"] = patch
    return suggestion


def requirement_suggestion_changes(version, suggestion, acceptance_criteria=None):
    current_title = str(version.get("title") or "").strip()
    current_content = str(
        version.get("plain_text_projection") or plain_text(version.get("content_doc", {})) or ""
    ).strip()
    revised_title = str(suggestion.get("revised_title") or "").strip()
    revised_content = str(suggestion.get("revised_content") or "").strip()
    patch = suggestion.get("patch") if isinstance(suggestion.get("patch"), dict) else {}
    current_criteria = [acceptance_criterion_text(item) for item in (acceptance_criteria or [])]
    proposed_criteria = [
        acceptance_criterion_text(item) for item in patch.get("acceptance_criteria", [])
    ]
    return bool(
        revised_title
        and revised_title != current_title
        or revised_content
        and revised_content != current_content
        or "actors" in patch
        and patch["actors"] != version.get("actors", [])
        or "business_rules" in patch
        and patch["business_rules"] != version.get("business_rules", [])
        or "dependencies" in patch
        and patch["dependencies"] != version.get("dependencies", [])
        or "acceptance_criteria" in patch
        and proposed_criteria != current_criteria
    )


def prepare_requirement_candidates(job_id, candidates):
    prepared = []
    for index, value in enumerate(candidates):
        candidate = dict(value)
        candidate["candidate_id"] = candidate.get("candidate_id") or (
            f"{job_id}{WORKFLOW_POLICY['candidate_suffix']}{index + 1}"
        )
        candidate["candidate_status"] = WORKFLOW_POLICY["active_candidate_status"]
        candidate["candidate_revision"] = int(
            candidate.get("candidate_revision", WORKFLOW_POLICY["initial_candidate_revision"])
        )
        candidate["parent_candidate_ids"] = list(candidate.get("parent_candidate_ids", []))
        prepared.append(candidate)
    return prepared


def candidate_fingerprint(candidate):
    return hashlib.sha256(
        serialized_content(
            {
                "candidate_id": candidate.get("candidate_id"),
                "title": candidate.get("title"),
                "content_doc": candidate.get("content_doc"),
                "source_refs": candidate.get("source_refs", []),
            }
        ).encode("utf-8")
    ).hexdigest()
