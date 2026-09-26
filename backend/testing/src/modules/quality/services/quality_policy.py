import json
from functools import lru_cache
from pathlib import Path

from src.core.common import plain_text


@lru_cache(maxsize=1)
def quality_policy():
    path = Path(__file__).resolve().parents[1] / "policies" / "quality_rules.json"
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def evaluate_rules(scope, value):
    findings = []
    for rule in quality_policy().get(scope, []):
        if evaluate_condition(rule.get("condition", {}), value):
            finding = {
                "rule_id": rule["rule_id"],
                "severity": rule["severity"],
                "span": None,
                "message": format_value(rule["message"], value),
                "suggestion": format_value(rule["suggestion"], value),
            }
            if rule.get("target_field"):
                finding["target_field"] = rule["target_field"]
            for key in ("category", "reason_code"):
                if rule.get(key):
                    finding[key] = rule[key]
            findings.append(finding)
    return findings


def evaluate_condition(condition, value):
    if "all" in condition:
        return all(evaluate_condition(item, value) for item in condition["all"])
    if "any" in condition:
        return any(evaluate_condition(item, value) for item in condition["any"])
    if "not" in condition:
        return not evaluate_condition(condition["not"], value)
    if "text_empty" in condition:
        return not text_value(resolve(value, condition["text_empty"]))
    if "values_empty" in condition:
        return not normalized_values(resolve(value, condition["values_empty"]))
    if "collection_values_empty" in condition:
        specification = condition["collection_values_empty"]
        items = resolve(value, specification["path"]) or []
        return not any(
            normalized_values(resolve(item, specification["field"])) for item in items
        )
    return False


def resolve(value, path):
    current = value
    for part in str(path).split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def text_value(value):
    if isinstance(value, dict):
        return plain_text(value).strip()
    return str(value or "").strip()


def normalized_values(value):
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [item for item in values if text_value(item)]


def format_value(template, value):
    replacements = {
        key: str(item or "") for key, item in value.items() if not isinstance(item, dict)
    }
    return template.format_map(DefaultValues(replacements))


class DefaultValues(dict):
    def __missing__(self, key):
        return ""
