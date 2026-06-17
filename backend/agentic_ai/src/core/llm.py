from typing import Dict, Literal
from core.config import settings
from huggingface_hub import AsyncInferenceClient
from loguru import logger
from src.utils.hf import HFInferenceChat

AITier = Literal['BASIC', 'PRO', 'PREMIUM', 'admin']

_BASIC_MODEL = settings.QWEN_MODEL
_ADVANCED_MODEL = settings.LLAMA_MODEL

_TIER_MODEL_MAP: Dict[str, str] = {
    'BASIC': _BASIC_MODEL,
    'PRO': _ADVANCED_MODEL,
    'PREMIUM': _ADVANCED_MODEL,
    'admin': _ADVANCED_MODEL,
}


def resolve_model_for_tier(ai_tier: str, role: str = 'reader') -> str:
    if role == 'admin':
        return _ADVANCED_MODEL
    return _TIER_MODEL_MAP.get(ai_tier, _BASIC_MODEL)


class LLMTier:
    def __init__(self):
        self._cache: Dict[str, HFInferenceChat] = {}

    def get_llm(self, ai_tier: str = 'BASIC', role: str = 'reader') -> HFInferenceChat:
        model = resolve_model_for_tier(ai_tier, role)
        cached = self._cache.get(model)
        if cached is not None:
            return cached
        try:
            client = AsyncInferenceClient(model=model, token=settings.HF_TOKEN)
            instance = HFInferenceChat(client=client, model=model)
            self._cache[model] = instance
            logger.info(f'llm_factory_initialized model={model}')
            return instance
        except Exception:
            logger.exception(f'llm_factory_init_failed model={model}')
            fallback_model = _ADVANCED_MODEL if model == _BASIC_MODEL else _BASIC_MODEL
            fallback_cached = self._cache.get(fallback_model)
            if fallback_cached is not None:
                return fallback_cached
            client = AsyncInferenceClient(model=fallback_model, token=settings.HF_TOKEN)
            instance = HFInferenceChat(client=client, model=fallback_model)
            self._cache[fallback_model] = instance
            return instance

    def get_basic_llm(self) -> HFInferenceChat:
        return self.get_llm('BASIC')

    def get_advanced_llm(self) -> HFInferenceChat:
        return self.get_llm('PREMIUM')


llm_tier = LLMTier()