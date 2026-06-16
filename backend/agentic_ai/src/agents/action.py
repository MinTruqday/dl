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
                return "The intelligent routing mechanism could not discover suitable functional API execution tool mapping"

            tool_call = result.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            tool_instance = next((t for t in tools if t.name == tool_name), None)
            if not tool_instance:
                return "The system routing architecture failed executing designated explicitly authorized networking software utility"

            config = {"configurable": {"token": token}}
            tool_res = await tool_instance.ainvoke(tool_args, config=config)
            logger.info("The operational diagnostic utility precisely executed mapped administrative transactional modification database queries")
            return str(tool_res)
        except Exception:
            logger.error("The programmatic procedural evaluation system crashed dispatching complex active structural tool invocations")
            return "The system encountered an unexpected error and requires you to try again later"

action = ActionAgent()