import json
from langchain_core.messages import HumanMessage
from loguru import logger
from src.core.prompts import PromptType, prompt_registry
from src.workflow.graph import llm

class SemanticRouter:
    async def execute(self, query: str) -> dict:
        try:
            prompt = prompt_registry.get(PromptType.PRIMARY_ROUTER).format(question=query)
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            raw = result.content.strip()
            
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
                
            parsed = json.loads(raw)
            logger.info("Lỗi xử lý model AI")
            return {"route": parsed.get("route", "rag"), "answer": parsed.get("answer", "")}
        except Exception:
            logger.error("Lỗi truy xuất cơ sở dữ liệu hệ thống")
            return {"route": "rag", "answer": ""}

semantic_router = SemanticRouter()