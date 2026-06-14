import json

from core.config import settings
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry
from src.tools.api_tools import llm, tools


class Action:
    def __init__(self):
        self.base_url = settings.INTERNAL_API_URL
        self.tool_map = {t.name: t for t in tools}

        tool_descriptions = []
        for t in tools:
            args = ""
            if hasattr(t, "args_schema") and t.args_schema:
                schema = t.args_schema.schema()
                props = schema.get("properties", {})
                args = ", ".join([f"{k}: {v.get('type')}" for k, v in props.items()])
            tool_descriptions.append(f"- {t.name}({args}): {t.description}")
        self.tools_prompt = "\n".join(tool_descriptions)

    async def execute(
        self, action: str, params: dict, user_id: str, token: str = None
    ) -> str:
        if not token and action != "public_query":
            return "Please log in to perform this action"

        system_prompt = prompt_registry.get(PromptType.TOOL_DISPATCHER)

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=action),
            ]

            llm_with_tools = llm.bind_tools(tools)

            for attempt in range(3):
                res = await llm_with_tools.ainvoke(messages)

                if not res.tool_calls:
                    return "No suitable tool found to process this request"

                tool_call = res.tool_calls[0]
                tool_name = tool_call["name"]
                tool_params = tool_call["args"]

                if tool_name not in self.tool_map:
                    return "Tool '{tool_name}' not found or does not exist"

                selected_tool = self.tool_map[tool_name]

                REQUIRES_APPROVAL_TOOLS = [
                    "delete_document",
                    "restore_document",
                    "create_document",
                    "send_virtual_tip",
                    "redeem_coupon",
                ]
                if tool_name in REQUIRES_APPROVAL_TOOLS:
                    return f"Task {tool_name} requires your approval to continue"

                logger.info("Calling tool '{tool_name}' with parameters {tool_params}")

                try:
                    tool_result = await selected_tool.ainvoke(
                        tool_params, config={"configurable": {"token": token}}
                    )
                    return str(tool_result)
                except Exception as e:
                    from langchain_core.messages import ToolMessage

                    messages.append(res)
                    messages.append(
                        ToolMessage(
                            content=f"Error executing tool {str(e)}, please check the data sent to the tool",
                            tool_call_id=tool_call["id"],
                        )
                    )
                    logger.warning("Tool encountered an issue, retrying attempt {attempt+1}/3")
                    if attempt == 2:
                        return f"Error executing operation after 3 attempts: {str(e)}"

        except Exception as e:
            logger.error("Task execution encountered an issue due to error")
            return "The system encountered an issue, please try again later"


action = Action()
