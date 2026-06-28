import json

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from src.core.registry import PromptType, registry
from src.tools.interface import llm, tools

from src.core.infrastructure.configuration import settings

class ActingAgent:
    def __init__(self):
        self.base_url = settings.INTERNAL_API_URL
        self.tool_map = {t.name: t for t in tools}

        tool_descriptions = []
        for t in tools:
            args = ""
            if hasattr(t, "args_schema") and t.args_schema:
                schema = t.args_schema.schema()
                props = schema.get("properties", {})
                args = ", ".join(
                    [f"{k} type {v.get('type')}" for k, v in props.items()]
                )
            tool_descriptions.append(f"- {t.name}({args}) {t.description}")
        self.tools_prompt = "\n".join(tool_descriptions)

    async def execute(
        self, action: str, params: dict, user_id: str, token: str = None
    ) -> str:
        if not token and action != "public_query":
            return "Bạn cần phải xác thực danh tính để tiếp tục"

        system_prompt = registry.get(PromptType.TOOL_DISPATCHER)

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=action),
            ]

            llm_with_tools = llm.bind_tools(tools)

            for attempt in range(3):
                res = await llm_with_tools.ainvoke(messages)

                if not res.tool_calls:
                    return "Hệ thống AI không tìm ra được công cụ thích hợp để xử lý yêu cầu này"

                tool_call = res.tool_calls[0]
                tool_name = tool_call["name"]
                tool_params = tool_call["args"]

                if tool_name not in self.tool_map:
                    return "Tiện ích mà bạn yêu cầu hiện không khả dụng hoặc không tồn tại"

                selected_tool = self.tool_map[tool_name]

                REQUIRES_APPROVAL_TOOLS = [
                    "delete_document",
                    "restore_document",
                    "create_document",
                    "send_virtual_tip",
                    "redeem_coupon",
                ]
                if tool_name in REQUIRES_APPROVAL_TOOLS:
                    return "Thao tác này bắt buộc phải có sự xác nhận ủy quyền trực tiếp từ người dùng"

                logger.info("Đang khởi chạy tiện ích")

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
                            content="The system encountered an error while executing the utility and requests a verification of the input data",
                            tool_call_id=tool_call["id"],
                        )
                    )
                    logger.exception("Gặp sự cố khi xử lý dữ liệu, hệ thống đang tự động thử lại")
                    if attempt == 2:
                        return "Thao tác vẫn không thành công mặc dù hệ thống đã nỗ lực thử lại nhiều lần"

        except Exception as e:
            logger.exception("Quá trình thực thi bị gián đoạn")
            return f"Đã xảy ra lỗi trong quá trình thực thi lệnh, vui lòng thử lại sau giây lát: {e}"

actor = ActingAgent()
