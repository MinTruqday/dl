import json
from langchain_core.messages import HumanMessage
from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry
from src.workflow.brain import llm

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
            logger.info("The primary intent classification neural routing module decisively allocated explicit appropriate processing")
            return {"route": parsed.get("route", "rag"), "answer": parsed.get("answer", "")}
        except Exception:
            logger.error("The semantic primary routing evaluation matrix catastrophically failed evaluating exact intent vectors")
            return {"route": "rag", "answer": ""}

semantic_router = SemanticRouter()