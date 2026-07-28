import re
from dataclasses import dataclass, field
from loguru import logger
from typing import List

@dataclass
class ScanResult:
    passed: bool
    risk_score: float
    sanitized_text: str
    blocked: bool = False
    violations: List[str] = field(default_factory=list)

class SecurityHarness:
    """
    <module_purpose>
    DocLib Security Harness for runtime prompt injection detection and content sanitization.
    </module_purpose>
    <contract>
    - Precondition: Raw input text from users or external sources.
    - Postcondition: Returns a sanitized string and scan result indicating if it was blocked.
    - Error Handling: Defaults to strict blocking if the security analysis engine fails.
    </contract>
    """
    def __init__(self):
        self.analyzer = None
        self.anonymizer = None
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            provider = NlpEngineProvider(
                nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [
                        {"lang_code": "en", "model_name": "en_core_web_sm"}
                    ],
                }
            )
            self.analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())
            self.anonymizer = AnonymizerEngine()
            logger.info("Presidio security engines initialized")
        except ImportError:
            logger.warning("Presidio dependencies unavailable, using deterministic PII scanning")
        except Exception:
            logger.exception("Presidio initialization failed, using deterministic PII scanning")

    async def _adetect_security_issues(
        self, text: str, allow_ai_review: bool = True
    ) -> tuple[str, List[str]]:
        from huggingface_hub import AsyncInferenceClient
        from langchain_core.messages import HumanMessage
        from src.utils.huggingface import HFInferenceChat
        from src.core.infrastructure.configuration import settings
        from src.schemas.security import SecurityEvaluation
        from src.core.registry import PromptType, registry
        
        violations = []
        sanitized = text

        pii_patterns = (
            (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[PII_EMAIL]"),
            (r"(?<!\w)\+?[1-9]\d(?:[\s().-]?\d){7,14}(?!\w)", "[PII_PHONE]"),
            (r"\b(?:\d[ -]*?){13,19}\b", "[PII_CARD]"),
        )
        for pattern, replacement in pii_patterns:
            updated = re.sub(pattern, replacement, sanitized)
            if updated != sanitized:
                violations.append("pii_detected")
                sanitized = updated

        injection_patterns = (
            r"ignore\s+(?:all\s+)?previous\s+instructions",
            r"reveal\s+(?:the\s+)?system\s+prompt",
            r"system\s+override",
            r"forget\s+(?:all|everything)",
            r"print\s+(?:your\s+)?initial\s+prompt",
        )
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in injection_patterns):
            violations.append("prompt_injection:deterministic_pattern")

        credential_patterns = (
            r"\bAKIA[0-9A-Z]{16}\b",
            r"\b(?:api[_-]?key|password|secret)\s*[:=]\s*[^\s]{8,}",
            r"\b(?:mongodb|postgres(?:ql)?|mysql|redis)://[^\s]+",
        )
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in credential_patterns):
            violations.append("credential_leak")

        if self.analyzer and self.anonymizer:
            try:
                results = self.analyzer.analyze(text=sanitized, entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "CRYPTO"], language='en')
                if results:
                    violations.append("pii_detected")
                    anonymized_result = self.anonymizer.anonymize(text=sanitized, analyzer_results=results)
                    sanitized = anonymized_result.text
            except Exception:
                logger.exception("Presidio scan failed")

        requires_ai_review = bool(sanitized.strip())
        if (
            not allow_ai_review
            or not requires_ai_review
            or any("credential_leak" in violation for violation in violations)
        ):
            return sanitized, list(dict.fromkeys(violations))

        try:
            client = AsyncInferenceClient(model=settings.LLM_MODEL, token=settings.HF_TOKEN)
            llm = HFInferenceChat(client=client, model=settings.LLM_MODEL)
            structured_llm = llm.with_structured_output(SecurityEvaluation)
            
            prompt = registry.get(PromptType.SECURITY_SCAN).format(text=sanitized)
            
            result = await structured_llm.ainvoke([HumanMessage(content=prompt)])
            if result.is_malicious:
                violations.append(f"prompt_injection:{result.reason[:60]}")
            if result.has_credentials:
                violations.append("credential_leak")
            if result.has_pii and "pii_detected" not in violations:
                violations.append("pii_detected")
                if result.sanitized_text:
                    sanitized = result.sanitized_text
        except Exception:
            logger.exception("AI security tracing failed")
            violations.append("security_classifier_unavailable")
            
        return sanitized, violations

    def _anomaly_score(self, text: str) -> float:
        if not text:
            return 0.0
        special_ratio = sum(
            1 for c in text if not c.isalnum() and not c.isspace()
        ) / max(len(text), 1)
        length_penalty = min(len(text) / 10000, 0.3)
        return min(special_ratio * 0.5 + length_penalty, 1.0)

    async def ascan_input(
        self,
        text: str,
        session_id: str = "",
        user_id: str = "",
        allow_ai_review: bool = True,
    ) -> ScanResult:
        """Inspect and sanitize inbound text with deterministic and optional model checks"""
        if not text or not text.strip():
            return ScanResult(passed=True, risk_score=0.0, sanitized_text=text or "")

        sanitized, violations = await self._adetect_security_issues(
            text,
            allow_ai_review=allow_ai_review,
        )
        
        injection_violations = [v for v in violations if "prompt_injection" in v]
        credential_violations = [v for v in violations if "credential_leak" in v]
        pii_violations = [v for v in violations if "pii" in v]
        
        anomaly = self._anomaly_score(text)
        injection_score = min(len(injection_violations) * 0.4, 1.0)
        risk_score = min(injection_score + anomaly * 0.2, 1.0)

        classifier_failures = [
            v for v in violations if "security_classifier_unavailable" in v
        ]

        if injection_violations or credential_violations or classifier_failures:
            logger.warning("Malicious command or credential leak blocked")
            return ScanResult(
                passed=False,
                blocked=True,
                risk_score=1.0,
                sanitized_text=sanitized,
                violations=violations,
            )

        if pii_violations:
            logger.info("System automatically obscured and protected sensitive PII")

        return ScanResult(
            passed=True,
            blocked=False,
            risk_score=risk_score,
            sanitized_text=sanitized,
            violations=violations,
        )

    async def ascan_output(self, text: str, session_id: str = "") -> str:
        if not text:
            return text
        sanitized, violations = await self._adetect_security_issues(
            text, allow_ai_review=False
        )
        sanitized = re.sub(
            r"<(think|thought)>.*?</\1>", "", sanitized, flags=re.IGNORECASE | re.DOTALL
        ).strip()
        if any("credential_leak" in v for v in violations):
            logger.error("System proactively blocked and neutralized credential leak risk")
            raise PermissionError("output_credential_leak_blocked")
        return sanitized

security = SecurityHarness()
