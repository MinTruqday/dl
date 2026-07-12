import re
import time
from typing import List

from loguru import logger
from src.core.registry import PromptType, registry

from src.harness.security import security

class GenerationAgent:
    def __init__(self):
        pass

    async def aggregate_stream(self, query: str, consolidated_results: List[str]):
        logger.info("Aggregating search results")

        scan = await security.ascan_input(query)
        if scan.blocked:
            logger.warning("Detected invalid operation")
            yield "Yêu cầu của bạn vi phạm chính sách bảo mật, hệ thống không thể tiếp tục xử lý"
            return

        try:
            from langchain_core.messages import HumanMessage
            from src.agents.planning import llm

            gathered_data = "\n\n".join(consolidated_results)
            if len(gathered_data) > 12000:
                gathered_data = gathered_data[:12000]

            final_prompt = registry.get(PromptType.AGGREGATOR).format(
                query=query, gathered_data=gathered_data
            )

            async for chunk in llm.astream([HumanMessage(content=final_prompt)]):
                if chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.exception("Error generating response content")
            yield f"Hệ thống đã gặp lỗi bất ngờ trong quá trình tạo phản hồi, vui lòng thử lại sau {e}"

response_generator = GenerationAgent()
