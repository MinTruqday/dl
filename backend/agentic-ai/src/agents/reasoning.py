from loguru import logger
from typing import List, Dict
import json
from langchain_huggingface import HuggingFaceEndpoint
from core.config import settings
from src.core.prompt_registry import prompt_registry, PromptType


class Reasoning:
    def __init__(self):
        self._model = settings.LLAMA_MODEL
        self._hf_token = settings.HF_TOKEN
        logger.info(f"Đã khởi tạo với mô hình{self._model}")

    async def execute(self, task: str) -> str:
        logger.info(f"Đang thực thi tác vụ suy luận: {task[:50]}")
        prompt = prompt_registry.get(PromptType.ANALYTICAL_ENGINE).format(task=task)
        try:
            from huggingface_hub import AsyncInferenceClient
            from src.utils.hf import HFInferenceChat
            from langchain_core.messages import HumanMessage
            client = AsyncInferenceClient(model=self._model, token=self._hf_token)
            llm = HFInferenceChat(client=client, model=self._model)
            
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            return result.content.strip()
        except Exception as e:
            logger.error(f"Thực thi thất bại do lỗi: {e}")
            return f"Lỗi suy luận: {str(e)}"

    async def evaluate_quality(self, query: str, answer: str, context_documents: List[Dict]) -> Dict:
        context_str = self._build_context(context_documents[:3])

        eval_prompt = prompt_registry.get(PromptType.QUALITY_EVALUATION).format(query=query, answer=answer, context_str=context_str[:3000])

        try:
            from huggingface_hub import AsyncInferenceClient
            from src.utils.hf import HFInferenceChat
            from langchain_core.messages import HumanMessage
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
        except Exception as e:
            logger.error(f"Đánh giá chất lượng thất bại do lỗi: {e}")
            return {"overall": 0.5, "should_retry": False, "feedback": f"Evaluation lỗi: {str(e)}"}

    def _build_context(self, documents: List[Dict]) -> str:
        if not documents:
            return "Không tìm thấy tài liệu phù hợp"

        parts = []
        for i, doc in enumerate(documents[:5], 1):
            title = doc.get("metadata", {}).get("title", "Unknown")
            author = doc.get("metadata", {}).get("author", "Unknown")
            text = doc.get("text", "")[:800]
            parts.append(f"[Source {i}] {title} - {author}\n{text}")

        return "\n\n".join(parts)

reasoning = Reasoning()
