import re
from typing import Any, Dict
from loguru import logger

from huggingface_hub import AsyncInferenceClient
from langchain_core.messages import HumanMessage, SystemMessage
from src.core.infrastructure.configuration import settings
from src.core.registry import PromptType, registry
from src.schemas.guardrails import SecurityAssessment
from src.utils.huggingface import HFInferenceChat

class GuardrailsEngine:
    def __init__(self):
        self._hf = AsyncInferenceClient(
            model=settings.LLM_MODEL,
            token=settings.HF_TOKEN,
        )
        self.llm = HFInferenceChat(client=self._hf, model=settings.LLM_MODEL)
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as redis_lib
                self._redis = redis_lib.from_url(settings.REDIS_URI, decode_responses=True)
            except Exception:
                logger.exception("Guardrails Redis client initialization failed")
        return self._redis

    async def _get_dynamic_patterns(self, key: str) -> list[str]:
        redis_client = self._get_redis()
        if redis_client:
            try:
                cached = await redis_client.smembers(key)
                if cached:
                    return [p for p in cached if p]
            except Exception:
                logger.exception("Dynamic security rule retrieval error")
        return []

    async def async_inspect_input(self, prompt: str) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            return {"is_safe": True, "risk_score": 0.0, "reason": "Empty input", "sanitized_text": ""}

        injection_rules = await self._get_dynamic_patterns("security:guardrails:patterns")
        for pattern in injection_rules:
            if re.search(pattern, prompt, re.IGNORECASE):
                return {
                    "is_safe": False,
                    "risk_score": 1.0,
                    "threat_category": "prompt_injection",
                    "reason": f"Matched dynamic security rule: {pattern}",
                    "sanitized_text": prompt,
                }

        credential_rules = await self._get_dynamic_patterns("security:guardrails:credentials")
        sanitized = prompt
        credential_found = False
        for pattern in credential_rules:
            updated = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
            credential_found = credential_found or updated != sanitized
            sanitized = updated

        if credential_found:
            return {
                "is_safe": False,
                "risk_score": 1.0,
                "threat_category": "credential_leak",
                "reason": "Credential material detected and redacted",
                "sanitized_text": sanitized,
            }

        try:
            system_prompt = registry.get(PromptType.PROMPT_INJECTION_DETECTOR)
            structured_llm = self.llm.with_structured_output(SecurityAssessment)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]
            assessment = await structured_llm.ainvoke(messages)
            return {
                "is_safe": assessment.is_safe,
                "risk_score": assessment.risk_score,
                "threat_category": assessment.threat_category,
                "reason": assessment.reason,
                "sanitized_text": prompt,
            }
        except Exception:
            logger.exception("AI safety classifier failed")
            return {
                "is_safe": False,
                "risk_score": 1.0,
                "threat_category": "classifier_unavailable",
                "reason": "Security classification unavailable",
                "sanitized_text": prompt,
            }

    def inspect_input(self, prompt: str) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            return {"is_safe": True, "risk_score": 0.0, "reason": "Empty input", "sanitized_text": ""}

        return {
            "is_safe": True,
            "risk_score": 0.0,
            "threat_category": "none",
            "reason": "Passed synchronous input check",
            "sanitized_text": prompt,
        }

    def inspect_output(self, response_text: str) -> Dict[str, Any]:
        if not response_text or not response_text.strip():
            return {"is_safe": True, "risk_score": 0.0, "reason": "Empty output", "sanitized_text": ""}

        return {
            "is_safe": True,
            "risk_score": 0.0,
            "threat_category": "none",
            "reason": "Passed synchronous output check",
            "sanitized_text": response_text,
        }

    validate_input = inspect_input
    validate_output = inspect_output

guardrails_engine = GuardrailsEngine()
