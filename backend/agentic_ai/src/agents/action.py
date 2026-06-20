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
                args = ", ".join([f"{k} type {v.get('type')}" for k, v in props.items()])
            tool_descriptions.append(f"- {t.name}({args}) {t.description}")
        self.tools_prompt = "\n".join(tool_descriptions)

    async def execute(
        self, action: str, params: dict, user_id: str, token: str = None
    ) -> str:
        if not token and action != "public_query":
            return "Authentication is required to proceed with this specific operation"

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
                    return "The system could not identify a suitable utility to process the given request"

                tool_call = res.tool_calls[0]
                tool_name = tool_call["name"]
                tool_params = tool_call["args"]

                if tool_name not in self.tool_map:
                    return "The requested utility could not be found within the available system resources"

                selected_tool = self.tool_map[tool_name]

                REQUIRES_APPROVAL_TOOLS = [
                    "delete_document",
                    "restore_document",
                    "create_document",
                    "send_virtual_tip",
                    "redeem_coupon",
                ]
                if tool_name in REQUIRES_APPROVAL_TOOLS:
                    return "The requested operation requires explicit user authorization before proceeding"

                logger.info("Đang khởi chạy tiện ích")

                try:
                    tool_result = await selected_tool.ainvoke(
                        tool_params, config={"configurable": {"token": token}}
                    )
                    return str(tool_result)
                except Exception:
                    from langchain_core.messages import ToolMessage

                    messages.append(res)
                    messages.append(
                        ToolMessage(
                            content="The system encountered an error while executing the utility and requests a verification of the input data",
                            tool_call_id=tool_call["id"],
                        )
                    )
                    logger.warning("Lỗi hệ thống, đang thử lại")
                    if attempt == 2:
                        return "The operation failed to complete successfully after exhausting all available retry attempts"

        except Exception:
            logger.error("Quá trình thực thi bị gián đoạn")
            return "The system encountered an unexpected error during the execution phase and requires you to try again later"


action = Action()