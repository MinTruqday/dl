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
    def __init__(self):
        pass

    async def _adetect_security_issues(self, text: str) -> tuple[str, List[str]]:
        from huggingface_hub import AsyncInferenceClient
        from langchain_core.messages import HumanMessage
        from src.utils.huggingface import HFInferenceChat
        from src.core.infrastructure.configuration import settings
        from src.schemas.model import SecurityEvaluation
        from src.core.registry import PromptType, registry
        
        violations = []
        sanitized = text
        try:
            client = AsyncInferenceClient(model=settings.LLAMA_MODEL, token=settings.HF_TOKEN)
            llm = HFInferenceChat(client=client, model=settings.LLAMA_MODEL)
            structured_llm = llm.with_structured_output(SecurityEvaluation)
            
            prompt = registry.get(PromptType.SECURITY_SCAN).format(text=text)
            
            result = await structured_llm.ainvoke([HumanMessage(content=prompt)])
            if result.is_malicious:
                violations.append(f"prompt_injection:{result.reason[:60]}")
            if result.has_credentials:
                violations.append("credential_leak")
            if result.has_pii:
                violations.append("pii_detected")
            
            sanitized = result.sanitized_text or text
        except Exception as e:
            logger.exception("Truy vết bảo mật AI thất bại")
            
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
        pii_violations = [v for v in violations if "pii" in v]
        
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
                violations=violations,
            )

        if pii_violations:
            logger.info("Hệ thống đã tự động làm mờ và bảo vệ các thông tin cá nhân nhạy cảm")

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
            logger.error("Hệ thống đã chủ động ngăn chặn và vô hiệu hóa thành công nguy cơ rò rỉ dữ liệu nhạy cảm")
            return "Nội dung phản hồi đã bị hệ thống an ninh chặn lại do phát hiện có chứa dữ liệu nhạy cảm"
        return sanitized

security = SecurityHarness()
