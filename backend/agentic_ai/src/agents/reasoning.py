import json
from typing import Dict, List

from core.config import settings
from langchain_huggingface import HuggingFaceEndpoint
from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry


class Reasoning:
    def __init__(self):
        self._model = settings.LLAMA_MODEL
        self._hf_token = settings.HF_TOKEN
        logger.info("The analytical reasoning engine was initialized successfully")

    async def execute(self, task: str) -> str:
        logger.info("The system is currently executing the requested inference task")
        prompt = prompt_registry.get(PromptType.ANALYTICAL_ENGINE).format(task=task)
        try:
            from huggingface_hub import AsyncInferenceClient
            from langchain_core.messages import HumanMessage
            from src.utils.hf import HFInferenceChat

            client = AsyncInferenceClient(model=self._model, token=self._hf_token)
            llm = HFInferenceChat(client=client, model=self._model)

            result = await llm.ainvoke([HumanMessage(content=prompt)])
            return result.content.strip()
        except Exception:
            logger.error("The inference task execution failed due to an unexpected internal error")
            return "The system encountered an error during the inference process"

    async def evaluate_quality(
        self, query: str, answer: str, context_documents: List[Dict]
    ) -> Dict:
        context_str = self._build_context(context_documents[:3])

        eval_prompt = prompt_registry.get(PromptType.QUALITY_EVALUATION).format(
            query=query, answer=answer, context_str=context_str[:3000]
        )

        try:
            from huggingface_hub import AsyncInferenceClient
            from langchain_core.messages import HumanMessage
            from src.utils.hf import HFInferenceChat

            client = AsyncInferenceClient(model=self._model, token=self._hf_token)
            llm = HFInferenceChat(client=client, model=self._model)

            result_text = await llm.ainvoke([HumanMessage(content=eval_prompt)])
            result_text = result_text.content.strip()

            if "```" in result_text:
                parts = result_text.split("```")
                for p in parts:
                    p = p.strip()
                    if p.startswith("json"):
                        result_text = p[4:].strip()
                        break
                    elif p.startswith("{"):
                        result_text = p
                        break

            return json.loads(result_text)
        except Exception:
            logger.error("The quality evaluation process encountered an unexpected failure")
            return {
                "overall": 0.5,
                "should_retry": False,
                "feedback": "The system encountered an error during the quality evaluation phase",
            }

    def _build_context(self, documents: List[Dict]) -> str:
        if not documents:
            return "The system could not locate any matching documents within the knowledge base"

        parts = []
        for i, doc in enumerate(documents[:5], 1):
            title = doc.get("metadata", {}).get("title", "Unknown")
            author = doc.get("metadata", {}).get("author", "Unknown")
            text = doc.get("text", "")[:800]
            parts.append(f"Source Document {i} {title} authored by {author}\n{text}")

        return "\n\n".join(parts)


reasoning = Reasoning()