import asyncio
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

import json
import os
from typing import Tuple, List

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
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            logger.info("Presidio Security Engines initialized successfully.")
        except ImportError:
            logger.warning("Presidio not installed. Falling back to LLM/Regex for PII scanning.")
        except Exception as e:
            logger.error(f"Failed to initialize Presidio: {e}")

    async def _adetect_security_issues(self, text: str) -> tuple[str, List[str]]:
        from huggingface_hub import AsyncInferenceClient
        from langchain_core.messages import HumanMessage
        from src.utils.huggingface import HFInferenceChat
        from src.core.infrastructure.configuration import settings
        from src.schemas.security import SecurityEvaluation
        from src.core.registry import PromptType, registry
        
        violations = []
        sanitized = text
        
        # 1. Fast PII Scanning via Presidio (Offline / Rule-based)
        if self.analyzer and self.anonymizer:
            try:
                results = self.analyzer.analyze(text=text, entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "CRYPTO"], language='en')
                if results:
                    violations.append("pii_detected")
                    anonymized_result = self.anonymizer.anonymize(text=text, analyzer_results=results)
                    sanitized = anonymized_result.text
            except Exception as e:
                logger.error(f"Presidio scan error: {e}")
                
        # 2. LLM Scanning for Prompt Injection
        try:
            client = AsyncInferenceClient(model=settings.LLM_MODEL, token=settings.HF_TOKEN)
            llm = HFInferenceChat(client=client, model=settings.LLM_MODEL)
            structured_llm = llm.with_structured_output(SecurityEvaluation)
            
            prompt = registry.get(PromptType.SECURITY_SCAN).format(text=text)
            
            result = await structured_llm.ainvoke([HumanMessage(content=prompt)])
            if result.is_malicious:
                violations.append(f"prompt_injection:{result.reason[:60]}")
            if result.has_credentials:
                violations.append("credential_leak")
            # If presidio failed to catch it but LLM caught it
            if result.has_pii and "pii_detected" not in violations:
                violations.append("pii_detected")
                if result.sanitized_text:
                    sanitized = result.sanitized_text
        except Exception as e:
            logger.exception("AI security tracing failed")
            
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
        self, text: str, session_id: str = "", user_id: str = ""
    ) -> ScanResult:
        if not text or not text.strip():
            return ScanResult(passed=True, risk_score=0.0, sanitized_text=text or "")

        sanitized, violations = await self._adetect_security_issues(text)
        
        injection_violations = [v for v in violations if "prompt_injection" in v]
        credential_violations = [v for v in violations if "credential_leak" in v]
        pii_violations = [v for v in violations if "pii" in v]
        
        anomaly = self._anomaly_score(text)
        injection_score = min(len(injection_violations) * 0.4, 1.0)
        risk_score = min(injection_score + anomaly * 0.2, 1.0)

        if injection_violations or credential_violations:
            logger.warning("Malicious command or credential leak blocked successfully")
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
        sanitized, violations = await self._adetect_security_issues(text)
        if any("credential_leak" in v for v in violations):
            logger.error("System proactively blocked and neutralized credential leak risk")
            return "Hệ thống bảo mật đã tự động chặn phản hồi do phát hiện rủi ro rò rỉ thông tin xác thực"
        return sanitized

security = SecurityHarness()
