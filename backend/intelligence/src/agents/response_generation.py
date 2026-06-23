import re
import time
from typing import List

from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry

from src.harness.security_guardrails import security


class ResponseGeneration:
    def __init__(self):
        pass

    async def aggregate_stream(self, query: str, consolidated_results: List[str]):
        logger.info("Đang tổng hợp kết quả tìm kiếm")

        scan = await security.ascan_input(query)
        if scan.blocked:
            logger.warning("Phát hiện thao tác không hợp lệ")
            yield "The submitted request violates the security policies and cannot be processed further"
            return

        try:
            from langchain_core.messages import HumanMessage
            from src.agents.tasks_plans import llm

            gathered_data = "\n\n".join(consolidated_results)
            if len(gathered_data) > 12000:
                gathered_data = gathered_data[:12000]

            final_prompt = prompt_registry.get(PromptType.AGGREGATOR).format(
                query=query, gathered_data=gathered_data
            )

            async for chunk in llm.astream([HumanMessage(content=final_prompt)]):
                if chunk.content:
                    yield chunk.content

        except Exception:
            logger.error("Lỗi tạo nội dung phản hồi")
            yield "The system encountered an unexpected error during the response generation process and requires you to try again later"


response_generator = ResponseGeneration()
