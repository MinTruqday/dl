import re
import time
from typing import List

from loguru import logger
from src.core.registry import PromptType, registry

from src.harness.security import security

class GenerationAgent:
    """
    <module_purpose>
    DocLib Generation Agent for handling final text generation from search results.
    </module_purpose>
    <contract>
    - Precondition: Consolidated search results and an unblocked user query.
    - Postcondition: Aggregates findings into formal output streamed back to the user.
    - Error Handling: Aborts immediately with a safety message if security scans fail.
    </contract>
    """
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
            from huggingface_hub import AsyncInferenceClient
            from src.utils.huggingface import HFInferenceChat
            from src.core.infrastructure.configuration import settings

            client = AsyncInferenceClient(model=settings.LLM_MODEL, token=settings.HF_TOKEN)
            llm = HFInferenceChat(client=client, model=settings.LLM_MODEL)

            gathered_data = "\n\n".join(consolidated_results)
            if len(gathered_data) > 12000:
                gathered_data = gathered_data[:12000]

            final_prompt = registry.get(PromptType.AGGREGATOR).format(
                query=query, gathered_data=gathered_data
            )

            try:
                async for chunk in llm.astream([HumanMessage(content=final_prompt)]):
                    if chunk.content:
                        yield chunk.content
            except RuntimeError as e:
                if "StopIteration" in str(e):
                    logger.warning("StopIteration during final generation")
                    yield "Hệ thống đang gặp lỗi khi tạo phản hồi"
                else:
                    raise

        except Exception:
            logger.exception("Error generating response content")
            yield "Hệ thống đã gặp lỗi bất ngờ trong quá trình tạo phản hồi, vui lòng thử lại sau"

response_generator = GenerationAgent()
