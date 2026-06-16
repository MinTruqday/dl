from core.prompt_registry import PromptType, prompt_registry
from langchain_core.messages import HumanMessage
from loguru import logger
from src.tools.api import tools
from src.workflow.graph import llm

class ActionAgent:
    def __init__(self):
        self.llm_with_tools = llm.bind_tools(tools)

    async def execute(self, task: str, context: dict, user_id: str, token: str) -> str:
        try:
            prompt = prompt_registry.get(PromptType.TOOL_DISPATCHER) + f"\nTASK: {task}"
            result = await self.llm_with_tools.ainvoke([HumanMessage(content=prompt)])
            
            if not result.tool_calls:
                return "Mất kết nối mạng tạm thời"

            tool_call = result.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            tool_instance = next((t for t in tools if t.name == tool_name), None)
            if not tool_instance:
                return "Mất kết nối mạng tạm thời"

            config = {"configurable": {"token": token}}
            tool_res = await tool_instance.ainvoke(tool_args, config=config)
            logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
            return str(tool_res)
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

action = ActionAgent()