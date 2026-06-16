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
            logger.info("The sophisticated analytical reasoning processor finalized evaluating deeply complex operational functional boundaries")
            return result.content
        except Exception:
            logger.error("The computational semantic reasoning mathematical matrix completely derailed avoiding analytical mapping structures")
            return "The system encountered an unexpected error and requires you to try again later"

    async def evaluate_quality(self, query: str, answer: str, context: list) -> dict:
        try:
            context_str = "\n".join([f"- {d.get('text', '')}" for d in context])
            prompt = prompt_registry.get(PromptType.QUALITY_EVALUATION).format(query=query, answer=answer, context_str=context_str)
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            raw = result.content.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            parsed = json.loads(raw)
            logger.info("The algorithmic quality assurance diagnostic protocol executed evaluating exact string contextual correctness")
            return parsed
        except Exception:
            logger.warning("The operational dynamic validation protocol missed parsing explicit rigid analytical JSON constraints")
            return {"should_retry": False}

reasoning = ReasoningAgent()