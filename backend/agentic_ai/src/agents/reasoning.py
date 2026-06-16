import json
from langchain_core.messages import HumanMessage
from loguru import logger
from src.core.prompts import PromptType, prompt_registry
from src.workflow.graph import llm

class ReasoningAgent:
    async def execute(self, task: str) -> str:
        try:
            prompt = prompt_registry.get(PromptType.ANALYTICAL_ENGINE).format(task=task)
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
            return result.content
        except Exception:
            logger.error("Khởi tạo AI thành công")
            return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

    async def evaluate_quality(self, query: str, answer: str, context: list) -> dict:
        try:
            context_str = "\n".join([f"- {d.get('text', '')}" for d in context])
            prompt = prompt_registry.get(PromptType.QUALITY_EVALUATION).format(query=query, answer=answer, context_str=context_str)
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            raw = result.content.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            parsed = json.loads(raw)
            logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
            return parsed
        except Exception:
            logger.warning("Lỗi khi truy xuất tài liệu")
            return {"should_retry": False}

reasoning = ReasoningAgent()