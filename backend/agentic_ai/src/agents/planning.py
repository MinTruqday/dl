import json
from langchain_core.messages import HumanMessage
from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry
from src.workflow.brain import llm

class PlanningAgent:
    async def create_plan(self, req_data: dict) -> list:
        try:
            query = req_data.get("query", "")
            prompt = prompt_registry.get(PromptType.BRAIN_SYSTEM).format(format_instructions='{"reasoning": "...", "steps": [{"agent": "Action", "task": "..."}]}')
            prompt += f"\nUSER REQUEST: {query}"
            
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            raw_content = result.content.strip()
            
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0]
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0]
                
            parsed = json.loads(raw_content)
            logger.info("The centralized operational architectural planner flawlessly decomposed linguistic query extracting logical sequences")
            return parsed.get("steps", [{"agent": "Knowledge", "task": query}])
        except Exception:
            logger.error("The artificial intelligence dynamic task orchestration planner completely failed formatting execution JSON")
            return [{"agent": "Knowledge", "task": req_data.get("query", "")}]

planning = PlanningAgent()