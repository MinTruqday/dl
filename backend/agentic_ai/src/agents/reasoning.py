from typing import Dict, List

from loguru import logger
from pydantic import BaseModel, Field
from src.core.registry import PromptType, registry

from src.core.infrastructure.configuration import settings

from src.schemas.evaluation import QualityEvaluation

class ReasoningAgent:
    """
    <module_purpose>
        <purpose>Provide deep analytical reasoning and critical assessment for complex logical queries.</purpose>
        <context>Invoked by the orchestration layer when a user query requires multi-step deduction (Zero-Shot CoT), quality evaluation, or deep thought.</context>
    </module_purpose>
    
    <contract>
        <input>Takes natural language tasks or context-augmented queries.</input>
        <output>Returns reasoned conclusions (str) or structured quality evaluations (Dict).</output>
        <exceptions>Returns an error string starting with MODULE REASONING_AGENT if LLM invocation fails.</exceptions>
    </contract>
    """
    def __init__(self):
        self._model = settings.LLM_MODEL
        self._hf_token = settings.HF_TOKEN

    async def execute(self, task: str) -> str:
        prompt = registry.get(PromptType.ANALYTICAL_ENGINE).format(task=task)
        try:
            from huggingface_hub import AsyncInferenceClient
            from langchain_core.messages import HumanMessage
            from src.utils.huggingface import HFInferenceChat

            client = AsyncInferenceClient(model=self._model, token=self._hf_token)
            llm = HFInferenceChat(client=client, model=self._model)
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            content = result.content.strip()
            
            if "</thought>" in content:
                final_answer = content.split("</thought>")[-1].strip()
                if final_answer:
                    return final_answer
            return content
        except Exception:
            logger.exception("Reasoning task execution error")
            return "Mô hình AI đang gặp trục trặc trong quá trình suy luận, vui lòng thử lại sau"

    async def evaluate_quality(
        self, query: str, answer: str, context_documents: List[Dict]
    ) -> Dict:
        context_str = self._build_context(context_documents[:3])
        eval_prompt = registry.get(PromptType.QUALITY_EVALUATION).format(
            query=query, answer=answer, context_str=context_str[:3000]
        )
        try:
            from huggingface_hub import AsyncInferenceClient
            from langchain_core.messages import HumanMessage
            from src.utils.huggingface import HFInferenceChat

            client = AsyncInferenceClient(model=self._model, token=self._hf_token)
            llm = HFInferenceChat(
                client=client, model=self._model
            ).with_structured_output(QualityEvaluation)

            eval_res: QualityEvaluation = await llm.ainvoke(
                [HumanMessage(content=eval_prompt)]
            )

            return {
                "should_retry": eval_res.is_hallucination,
                "feedback": eval_res.feedback,
            }
        except Exception as e:
            logger.exception("Document quality evaluation error")
            return {
                "should_retry": False,
                "feedback": "The system encountered an error during the quality evaluation phase",
            }

    def _build_context(self, documents: List[Dict]) -> str:
        if not documents:
            return "The current knowledge base does not contain any documents matching your required information"
        parts = []
        for i, doc in enumerate(documents[:5], 1):
            title = doc.get("metadata", {}).get("title", "Unknown")
            author = doc.get("metadata", {}).get("author", "Unknown")
            text = doc.get("text", "")[:800]
            parts.append(f"Source Document {i} {title} authored by {author}\n{text}")
        return "\n\n".join(parts)

reasoner = ReasoningAgent()
