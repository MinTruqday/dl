import re

from src.services.domain_policy import domain_policy


def secret_pattern():
    return re.compile(domain_policy("secret_detection")["field_name_pattern"], re.I)


def redact_sensitive_text(value):
    policy = domain_policy("secret_detection")
    replacement = policy["redacted_value"]
    result = re.sub(
        policy["url_value_pattern"],
        lambda match: f"{match.group(1)}{replacement}",
        value,
    )
    for pattern_name in ("raw_assignment_pattern", "inline_value_pattern"):
        result = re.sub(
            policy[pattern_name],
            lambda match: f"{match.group(1)}{match.group(2)}{replacement}",
            result,
            flags=re.I,
        )
    return result


def redact_sensitive_data(value):
    policy = domain_policy("secret_detection")
    if isinstance(value, dict):
        return {
            key: policy["redacted_value"]
            if secret_pattern().search(str(key))
            else redact_sensitive_data(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value
