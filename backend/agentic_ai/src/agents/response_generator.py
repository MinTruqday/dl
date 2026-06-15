from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry
from src.workflow.brain import llm

class ResponseGeneratorAgent:
    async def aggregate_stream(self, query: str, gathered_data: list) -> AsyncGenerator[str, None]:
        try:
            combined = "\n\n".join([str(d) for d in gathered_data])
            prompt = prompt_registry.get(PromptType.AGGREGATOR).format(query=query, gathered_data=combined)
            
            logger.info("The final linguistic synthesizing aggregator framework effectively engaged processing combined analytical stream")
            async for chunk in llm.astream([HumanMessage(content=prompt)]):
                if chunk.content:
                    yield chunk.content
        except Exception:
            logger.error("The automated linguistic synthesis sequence abruptly failed dispatching contiguous output streaming components")
            yield "The system encountered an unexpected error and requires you to try again later"

response_generator = ResponseGeneratorAgent()