from typing import Dict, List
from core.config import settings
from loguru import logger
from pydantic import BaseModel, Field
from src.core.prompt_registry import PromptType, prompt_registry

class QualityEvaluation(BaseModel):
    is_hallucination: bool = Field(description="True if the generated answer contains hallucinated facts or is not grounded in the documents, False otherwise")
    feedback: str = Field(description="Concise feedback explaining the reasoning")

class Reasoning:
    def __init__(self):
        self._model = settings.LLAMA_MODEL
        self._hf_token = settings.HF_TOKEN

    async def execute(self, task: str) -> str:
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
            logger.exception("The inference task execution failed due to an unexpected internal error")
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
            llm = HFInferenceChat(client=client, model=self._model).with_structured_output(QualityEvaluation)
            
            eval_res: QualityEvaluation = await llm.ainvoke([HumanMessage(content=eval_prompt)])
            
            return {
                "should_retry": eval_res.is_hallucination,
                "feedback": eval_res.feedback
            }
        except Exception:
            logger.exception("The quality evaluation process encountered an unexpected failure")
            return {
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