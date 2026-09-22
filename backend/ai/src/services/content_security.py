import re

from src.core.security.guardrails import security_rules


def prompt_injection_flags(text: str):
    return [
        f"prompt_injection_pattern_{index + 1}"
        for index, pattern in enumerate(security_rules()["prompt_injection_patterns"])
        if re.search(pattern, text, re.IGNORECASE)
    ]
