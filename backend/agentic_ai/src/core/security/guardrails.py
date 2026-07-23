import re
from typing import Any, Dict, List
from loguru import logger

class GuardrailsEngine:
    def __init__(self):
        self.injection_patterns = [
            r"ignore\s+previous\s+instructions",
            r"override\s+system\s+prompt",
            r"disregard\s+all\s+prior",
            r"you\s+are\s+now\s+an\s+unrestricted",
            r"dan\s+mode",
            r"system_prompt_override",
            r"rm\s+-rf\s+/",
            r"exec\s*\(\s*['\"]",
            r"eval\s*\(\s*['\"]"
        ]

    def inspect_input(self, prompt: str) -> Dict[str, Any]:
        if not prompt:
            return {"is_safe": True, "reason": "Empty input", "sanitized_text": ""}

        lowered = prompt.lower()
        for pattern in self.injection_patterns:
            if re.search(pattern, lowered):
                logger.warning(f"Guardrails detected suspicious prompt pattern: {pattern}")
                return {
                    "is_safe": False,
                    "reason": f"Suspicious prompt pattern detected: {pattern}",
                    "sanitized_text": prompt
                }

        return {
            "is_safe": True,
            "reason": "Input passed security guardrails",
            "sanitized_text": prompt
        }

    def inspect_output(self, response_text: str) -> Dict[str, Any]:
        if not response_text:
            return {"is_safe": True, "reason": "Empty output", "sanitized_text": ""}

        return {
            "is_safe": True,
            "reason": "Output passed security guardrails",
            "sanitized_text": response_text
        }

    validate_input = inspect_input
    validate_output = inspect_output

guardrails_engine = GuardrailsEngine()
