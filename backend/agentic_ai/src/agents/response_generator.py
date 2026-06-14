import re
import time
from typing import List

from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry

_INJECTION_PATTERN = re.compile(
    r"(system[_\s]?prompt|api[_\s]?key|secret[_\s]?key|hf[_\s]?token"
    r"|ignore (previous|above|all)|jailbreak|do anything now|dan mode"
    r"|bypass (safety|filter|restriction))",
    re.IGNORECASE,
)


def _contains_injection(text: str) -> bool:
    return bool(_INJECTION_PATTERN.search(text))


class ResponseGenerator:
    def __init__(self):
        pass

    async def aggregate_stream(self, query: str, consolidated_results: List[str]):
        logger.info(f"Synthesizing results for query: {query[:50]}")

        if _contains_injection(query):
            logger.warning("Detected potential prompt injection in query")
            yield "This request violates our usage policy. Please ask another question"
            return

        try:
            from langchain_core.messages import HumanMessage
            from src.agents.planning import llm

            gathered_data = "\n\n".join(consolidated_results)
            if len(gathered_data) > 12000:
                gathered_data = gathered_data[:12000]

            final_prompt = prompt_registry.get(PromptType.AGGREGATOR).format(
                query=query, gathered_data=gathered_data
            )

            async for chunk in llm.astream([HumanMessage(content=final_prompt)]):
                if chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            yield "The system encountered an issue, please try again later"


response_generator = ResponseGenerator()
