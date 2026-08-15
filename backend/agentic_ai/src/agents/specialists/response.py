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
    async def aggregate_stream(self, query: str, consolidated_results: List[str]):
        logger.info("Aggregating search results")

        scan = await security.ascan_input(query)
        if scan.blocked:
            logger.warning("Detected invalid operation")
            raise PermissionError("input_security_blocked")

        try:
            from langchain_core.messages import HumanMessage
            from src.utils.huggingface import create_chat_model

            llm = create_chat_model()

            gathered_data = "\n\n".join(consolidated_results)
            if len(gathered_data) > 12000:
                gathered_data = gathered_data[:12000]

            final_prompt = registry.get(PromptType.AGGREGATOR).format(
                query=query, gathered_data=gathered_data
            )

            async for chunk in llm.astream([HumanMessage(content=final_prompt)]):
                if chunk.content:
                    yield chunk.content

        except Exception:
            logger.exception("Error generating response content")
            raise RuntimeError("response_generation_failed")

response_generator = GenerationAgent()
