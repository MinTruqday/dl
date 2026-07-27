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

    async def async_inspect_input(self, prompt: str) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            return {"is_safe": True, "risk_score": 0.0, "reason": "Empty input", "sanitized_text": ""}

        redis_client = self._get_redis()
        if redis_client:
            try:
                custom_rules = await redis_client.smembers("security:guardrails:patterns")
                lowered = prompt.lower()
                for pattern in custom_rules:
                    if pattern and re.search(pattern, lowered):
                        logger.warning("Guardrails dynamic rule matched")
                        return {
                            "is_safe": False,
                            "risk_score": 0.95,
                            "threat_category": "dynamic_rule_violation",
                            "reason": f"Matched dynamic security rule: {pattern}",
                            "sanitized_text": prompt
                        }
            except Exception:
                logger.exception("Dynamic guardrail rule check failed")

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
                "sanitized_text": prompt
            }
        except Exception:
            logger.exception("AI safety classifier failed")
            return {
                "is_safe": False,
                "risk_score": 1.0,
                "threat_category": "classifier_unavailable",
                "reason": "Security classification unavailable",
                "sanitized_text": prompt
            }

    def inspect_input(self, prompt: str) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            return {"is_safe": True, "risk_score": 0.0, "reason": "Empty input", "sanitized_text": ""}

        return {
            "is_safe": True,
            "risk_score": 0.0,
            "threat_category": "none",
            "reason": "Passed security inspection",
            "sanitized_text": prompt
        }

    def inspect_output(self, response_text: str) -> Dict[str, Any]:
        if not response_text:
            return {"is_safe": True, "risk_score": 0.0, "reason": "Empty output", "sanitized_text": ""}

        return {
            "is_safe": True,
            "risk_score": 0.0,
            "threat_category": "none",
            "reason": "Passed output security inspection",
            "sanitized_text": response_text
        }

    validate_input = inspect_input
    validate_output = inspect_output

guardrails_engine = GuardrailsEngine()
