from typing import AsyncGenerator, List
from langchain_core.messages import HumanMessage
from loguru import logger
from src.core.llm_factory import llm_factory
from src.core.prompts import PromptType, prompt_registry

_FALLBACK_MESSAGE = 'Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau'
_EMPTY_MESSAGE = 'Hệ thống chưa thu thập đủ dữ liệu để hoàn thiện phản hồi cho yêu cầu của bạn'


class ResponseGeneratorAgent:
    async def aggregate_stream(self, query: str, gathered_data: List, ai_tier: str = 'BASIC', role: str = 'reader') -> AsyncGenerator[str, None]:
        if not gathered_data:
            yield _EMPTY_MESSAGE
            return
        try:
            combined = '\n\n---\n\n'.join(str(d) for d in gathered_data)[:18000]
            prompt = prompt_registry.get(PromptType.AGGREGATOR).format(query=query, gathered_data=combined)
            user_llm = llm_factory.get_llm(ai_tier, role)
            async for chunk in user_llm.astream([HumanMessage(content=prompt)]):
                token = getattr(chunk, 'content', '')
                if token:
                    yield token
        except Exception:
            logger.exception('response_generator_stream_failed')
            yield _FALLBACK_MESSAGE

    async def aggregate(self, query: str, gathered_data: List, ai_tier: str = 'BASIC', role: str = 'reader') -> str:
        if not gathered_data:
            return _EMPTY_MESSAGE
        try:
            combined = '\n\n---\n\n'.join(str(d) for d in gathered_data)[:18000]
            prompt = prompt_registry.get(PromptType.AGGREGATOR).format(query=query, gathered_data=combined)
            user_llm = llm_factory.get_llm(ai_tier, role)
            result = await user_llm.ainvoke([HumanMessage(content=prompt)])
            return result.content
        except Exception:
            logger.exception('response_generator_aggregate_failed')
            return _FALLBACK_MESSAGE


response_generator = ResponseGeneratorAgent()