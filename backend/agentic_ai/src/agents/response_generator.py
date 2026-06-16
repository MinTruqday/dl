from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from loguru import logger
from src.core.prompts import PromptType, prompt_registry
from src.workflow.graph import llm

class ResponseGeneratorAgent:
    async def aggregate_stream(self, query: str, gathered_data: list) -> AsyncGenerator[str, None]:
        try:
            combined = "\n\n".join([str(d) for d in gathered_data])
            prompt = prompt_registry.get(PromptType.AGGREGATOR).format(query=query, gathered_data=combined)
            
            logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
            async for chunk in llm.astream([HumanMessage(content=prompt)]):
                if chunk.content:
                    yield chunk.content
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            yield "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

response_generator = ResponseGeneratorAgent()