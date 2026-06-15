from core.prompt_registry import PromptType, prompt_registry
from langchain_core.messages import HumanMessage
from loguru import logger
from src.workflow.brain import llm

class CodeInterpreterAgent:
    async def execute(self, task: str) -> str:
        try:
            prompt = prompt_registry.get(PromptType.CODE_INTERPRETER) + f"\nTASK: {task}"
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            logger.info("The programmatic structural code compilation module seamlessly processed explicit textual algorithmic generation")
            return result.content
        except Exception:
            logger.error("The structural code interpreter algorithmic logic decisively crashed executing designated computational generation")
            return "The system encountered an unexpected error and requires you to try again later"

code_interpreter = CodeInterpreterAgent()