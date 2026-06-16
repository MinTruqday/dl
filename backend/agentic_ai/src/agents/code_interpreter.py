from core.prompt_registry import PromptType, prompt_registry
from langchain_core.messages import HumanMessage
from loguru import logger
from src.workflow.graph import llm

class CodeInterpreterAgent:
    async def execute(self, task: str) -> str:
        try:
            prompt = prompt_registry.get(PromptType.CODE_INTERPRETER) + f"\nTASK: {task}"
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
            return result.content
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

code_interpreter = CodeInterpreterAgent()