import json
from loguru import logger
from src.core.config import settings
from src.tools.actions import tools, llm
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.prompt_registry import prompt_registry, PromptType


class ToolDispatcher:
    def __init__(self):
        self.base_url = settings.INTERNAL_API_URL
        self.tool_map = {t.name: t for t in tools}
        
        tool_descriptions = []
        for t in tools:
            args = ""
            if hasattr(t, 'args_schema') and t.args_schema:
                schema = t.args_schema.schema()
                props = schema.get("properties", {})
                args = ", ".join([f"{k}: {v.get('type')}" for k, v in props.items()])
            tool_descriptions.append(f"- {t.name}({args}): {t.description}")
        self.tools_prompt = "\n".join(tool_descriptions)

    async def execute(self, action: str, params: dict, user_id: str, token: str = None) -> str:
        if not token and action != "public_query":
            return "Lỗi xác thực: Vui lòng đăng nhập để thực hiện thao tác với hệ thống."
            
        system_prompt = prompt_registry.get(PromptType.TOOL_DISPATCHER)

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=action)
            ]
            
            llm_with_tools = llm.bind_tools(tools)
            
            for attempt in range(3):
                res = await llm_with_tools.ainvoke(messages)
                
                if not res.tool_calls:
                    return "Từ chối thực thi: Hệ thống không có công cụ nào phù hợp để xử lý yêu cầu này."
                    
                tool_call = res.tool_calls[0]
                tool_name = tool_call["name"]
                tool_params = tool_call["args"]
                
                if tool_name not in self.tool_map:
                    return f"Từ chối thực thi: Công cụ '{tool_name}' không tồn tại."
                    
                selected_tool = self.tool_map[tool_name]
                
                REQUIRES_APPROVAL_TOOLS = ["delete_document", "restore_document", "create_document", "send_virtual_tip", "redeem_voucher"]
                if tool_name in REQUIRES_APPROVAL_TOOLS:
                    return f"[INTERRUPT] Tác vụ {tool_name} yêu cầu xác nhận. Hệ thống đang chờ phê duyệt từ người dùng."

                logger.info(f"ToolDispatcher: Invoking tool '{tool_name}' with params {tool_params}")
                
                try:
                    tool_result = await selected_tool.ainvoke(tool_params, config={"configurable": {"token": token}})
                    return str(tool_result)
                except Exception as e:
                    from langchain_core.messages import ToolMessage
                    messages.append(res)
                    messages.append(ToolMessage(content=f"Error executing tool: {str(e)}. Please fix the JSON payload and try again.", tool_call_id=tool_call["id"]))
                    logger.warning(f"ToolDispatcher: Tool failed, retrying ({attempt+1}/3): {e}")
                    if attempt == 2:
                        return f"Đã xảy ra lỗi khi thực thi thao tác sau 3 lần thử: {str(e)}"

                
        except Exception as e:
            logger.error(f"ToolDispatcher: Task execution failed: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

dispatcher = ToolDispatcher()
