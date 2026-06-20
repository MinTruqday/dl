import asyncio
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|context)",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions?",
    r"you\s+are\s+now\s+(a\s+)?(?!DocLib)",
    r"act\s+as\s+(?:if\s+you\s+are\s+)?(?:an?\s+)?(?:unrestricted|uncensored|evil|jailbreak)",
    r"(pretend|imagine|roleplay|simulate)\s+(you\s+are\s+|that\s+you\s+are\s+)?(?:a\s+)?(?:different|new|another)\s+(ai|assistant|model|system)",
    r"system\s*:\s*(you\s+are|ignore)",
    r"<\s*system\s*>",
    r"\[INST\].*ignore",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"bypass\s+(safety|filter|restriction|guardrail)",
    r"forget\s+(your|all)\s+(training|instructions?|rules?|constraints?)",
    r"print\s+(your\s+)?(system\s+)?(prompt|instructions?)",
    r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions?|context)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?)",
]

CREDENTIAL_LEAK_PATTERNS = [
    r"(password|passwd|pwd)\s*[=:]\s*\S+",
    r"(api[_-]?key|apikey|secret[_-]?key)\s*[=:]\s*[A-Za-z0-9_\-]{16,}",
    r"Bearer\s+[A-Za-z0-9\-._~+/]{20,}",
    r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+",
    r"(mongodb(\+srv)?://|postgresql://|mysql://)\S+:\S+@",
]

PII_PATTERNS = {
    "phone_vn": (r"\b(0[35789]\d{8}|\+84[35789]\d{8})\b", "[SDT_AN]"),
    "email": (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL_AN]"),
    "credit_card": (r"\b(?:\d[ \-]?){13,16}\b", "[CC_AN]"),
    "national_id_vn": (r"\b\d{9}(?:\d{3})?\b", "[CCCD_AN]"),
}


@dataclass
class ScanResult:
    passed: bool
    risk_score: float
    sanitized_text: str
    violations: list = field(default_factory=list)
    blocked: bool = False


class SecurityHarness:
    def __init__(self):
        self._compiled_injection = [
            re.compile(p, re.IGNORECASE | re.DOTALL) for p in PROMPT_INJECTION_PATTERNS
        ]
        self._compiled_credential = [
            re.compile(p, re.IGNORECASE) for p in CREDENTIAL_LEAK_PATTERNS
        ]
        self._compiled_pii = {
            name: (re.compile(pattern, re.IGNORECASE), replacement)
            for name, (pattern, replacement) in PII_PATTERNS.items()
        }

    def _detect_injection(self, text: str) -> list[str]:
        violations = []
        for pattern in self._compiled_injection:
            if pattern.search(text):
                violations.append(f"prompt_injection:{pattern.pattern[:40]}")
        return violations

    def _redact_pii(self, text: str) -> tuple[str, list[str]]:
        redacted = text
        found = []
        for name, (pattern, replacement) in self._compiled_pii.items():
            if pattern.search(redacted):
                found.append(f"pii:{name}")
                redacted = pattern.sub(replacement, redacted)
        return redacted, found

    def _detect_credential_leak(self, text: str) -> list[str]:
        violations = []
        for pattern in self._compiled_credential:
            if pattern.search(text):
                violations.append("credential_leak")
        return violations

    def _anomaly_score(self, text: str) -> float:
        if not text:
            return 0.0
        special_ratio = sum(
            1 for c in text if not c.isalnum() and not c.isspace()
        ) / max(len(text), 1)
        length_penalty = min(len(text) / 10000, 0.3)
        return min(special_ratio * 0.5 + length_penalty, 1.0)

    def scan_input(
        self, text: str, session_id: str = "", user_id: str = ""
    ) -> ScanResult:
        if not text or not text.strip():
            return ScanResult(passed=True, risk_score=0.0, sanitized_text=text or "")

        injection_violations = self._detect_injection(text)
        sanitized, pii_violations = self._redact_pii(text)
        all_violations = injection_violations + pii_violations
        anomaly = self._anomaly_score(text)

        injection_score = min(len(injection_violations) * 0.4, 1.0)
        risk_score = min(injection_score + anomaly * 0.2, 1.0)

        if injection_violations:
            logger.warning("Ngăn chặn lệnh độc hại thành công")
            return ScanResult(
                passed=False,
                blocked=True,
                risk_score=risk_score,
                sanitized_text=sanitized,
                violations=all_violations,
            )

        if pii_violations:
            logger.info("Đã ẩn thông tin cá nhân nhạy cảm")

        return ScanResult(
            passed=True,
            blocked=False,
            risk_score=risk_score,
            sanitized_text=sanitized,
            violations=all_violations,
        )

    def scan_output(self, text: str, session_id: str = "") -> str:
        if not text:
            return text
        credential_violations = self._detect_credential_leak(text)
        if credential_violations:
            logger.error("Ngăn chặn rò rỉ dữ liệu nhạy cảm")
            return "The response was blocked by the security system due to the detection of sensitive information"
        sanitized, _ = self._redact_pii(text)
        return sanitized


security_harness = SecurityHarness()