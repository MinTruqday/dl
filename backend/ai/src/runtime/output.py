import json
import re
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def output_policy():
    path = Path(__file__).with_name("output_policy.json")
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def normalize_narrative(value):
    text = str(value or "").strip()
    policy = output_policy()
    if not text or text in policy["reserved_field_names"]:
        return ""
    if any(re.search(pattern, text) for pattern in policy["invalid_patterns"]):
        return ""
    closing = ""
    while text and text[-1] in policy["closing_characters"]:
        closing = text[-1] + closing
        text = text[:-1].rstrip()
    return text.rstrip(policy["terminal_characters"] + " ") + closing


def normalize_narratives(values):
    normalized = [normalize_narrative(value) for value in values]
    return list(dict.fromkeys(value for value in normalized if value))


def normalize_narrative_payload(value, field_name=""):
    narrative_fields = set(output_policy()["narrative_fields"])
    if isinstance(value, dict):
        return {
            key: normalize_narrative_payload(item, key) for key, item in value.items()
        }
    if isinstance(value, list):
        if field_name in narrative_fields and all(isinstance(item, str) for item in value):
            return normalize_narratives(value)
        return [normalize_narrative_payload(item, field_name) for item in value]
    if isinstance(value, str) and field_name in narrative_fields:
        return normalize_narrative(value)
    return value
