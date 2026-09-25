import asyncio
import re
from dataclasses import dataclass, field
from typing import List

from loguru import logger

from src.core.security.guardrails import guardrails_engine, security_rules


@dataclass
class ScanResult:
    passed: bool
    risk_score: float
    sanitized_text: str
    blocked: bool = False
    violations: List[str] = field(default_factory=list)


class SecurityHarness:
    def __init__(self):
        self.analyzer = None
        self.anonymizer = None
        self._pii_engine_initialized = False
        self._pii_engine_lock = asyncio.Lock()

    def _initialize_pii_engine(self):
        pii_policy = security_rules()["pii"]
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            from presidio_anonymizer import AnonymizerEngine

            provider = NlpEngineProvider(
                nlp_configuration={
                    "nlp_engine_name": pii_policy["nlp_engine"],
                    "models": [
                        {
                            "lang_code": pii_policy["language"],
                            "model_name": pii_policy["model"],
                        }
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
        finally:
            self._pii_engine_initialized = True

    async def _ensure_pii_engine(self):
        if self._pii_engine_initialized:
            return
        async with self._pii_engine_lock:
            if not self._pii_engine_initialized:
                await asyncio.to_thread(self._initialize_pii_engine)

    async def _adetect_security_issues(
        self, text: str, allow_ai_review: bool = True
    ) -> tuple[str, List[str]]:
        await self._ensure_pii_engine()
        from langchain_core.messages import HumanMessage, SystemMessage

        from src.core.registry import PromptType, registry
        from src.schemas.security import SecurityEvaluation
        from src.utils.huggingface import create_chat_model

        violations = []
        baseline = guardrails_engine.inspect_input(text)
        sanitized = baseline.get("sanitized_text", text)
        category = baseline.get("threat_category", "none")
        if category == "prompt_injection":
            violations.append("prompt_injection:baseline_rule")
        elif category == "credential_leak":
            violations.append("credential_leak")
        elif category == "pii":
            violations.append("pii_detected")

        if self.analyzer and self.anonymizer:
            try:
                results = self.analyzer.analyze(
                    text=sanitized,
                    entities=security_rules()["pii"]["entities"],
                    language=security_rules()["pii"]["language"],
                )
                if results:
                    violations.append("pii_detected")
                    anonymized_result = self.anonymizer.anonymize(
                        text=sanitized, analyzer_results=results
                    )
                    sanitized = anonymized_result.text
            except Exception:
                logger.exception("Presidio scan failed")

        normalized = sanitized.casefold()
        suspicious_markers = security_rules()["prompt_injection_markers"]
        requires_ai_review = category != "none" or any(
            marker in normalized for marker in suspicious_markers
        )
        if (
            not allow_ai_review
            or not requires_ai_review
            or any(
                marker in violation
                for violation in violations
                for marker in ("credential_leak", "prompt_injection")
            )
        ):
            return sanitized, list(dict.fromkeys(violations))

        try:
            llm = create_chat_model()
            structured_llm = llm.with_structured_output(SecurityEvaluation)

            system_prompt = registry.get(PromptType.SECURITY_SCAN)

            result = await structured_llm.ainvoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=sanitized)]
            )
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
        policy = security_rules()["anomaly"]
        special_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(
            len(text), 1
        )
        length_penalty = min(
            len(text) / policy["length_scale"], policy["length_penalty_cap"]
        )
        return min(special_ratio * policy["special_character_weight"] + length_penalty, 1.0)

    async def ascan_input(
        self, text: str, session_id: str = "", user_id: str = "", allow_ai_review: bool = True
    ) -> ScanResult:
        if not text or not text.strip():
            return ScanResult(passed=True, risk_score=0.0, sanitized_text=text or "")

        sanitized, violations = await self._adetect_security_issues(
            text, allow_ai_review=allow_ai_review
        )

        injection_violations = [v for v in violations if "prompt_injection" in v]
        credential_violations = [v for v in violations if "credential_leak" in v]
        pii_violations = [v for v in violations if "pii" in v]

        anomaly = self._anomaly_score(text)
        anomaly_policy = security_rules()["anomaly"]
        injection_score = min(
            len(injection_violations) * anomaly_policy["injection_violation_weight"], 1.0
        )
        risk_score = min(injection_score + anomaly * anomaly_policy["anomaly_weight"], 1.0)

        classifier_failures = [v for v in violations if "security_classifier_unavailable" in v]

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
        baseline = guardrails_engine.inspect_output(text)
        text = baseline.get("sanitized_text", text)
        if baseline.get("threat_category") == "credential_leak":
            raise PermissionError("output_credential_leak_blocked")
        sanitized, violations = await self._adetect_security_issues(text, allow_ai_review=False)
        sanitized = re.sub(
            security_rules()["hidden_reasoning_pattern"],
            "",
            sanitized,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()
        if any("credential_leak" in v for v in violations):
            logger.error("System proactively blocked and neutralized credential leak risk")
            raise PermissionError("output_credential_leak_blocked")
        return sanitized


security = SecurityHarness()
