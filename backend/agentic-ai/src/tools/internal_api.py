import json
from loguru import logger
from src.core.config import settings
from src.agents.action import auth_token_var, tools, llm
from langchain_core.messages import SystemMessage, HumanMessage

class InternalAPIAgent:
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
        token = token or auth_token_var.get()
        if token:
            auth_token_var.set(token)
        logger.info(f"InternalAPI: Executing action {action} for user {user_id} with explicit token")
        if not token and action != "public_query":
            return "Lỗi xác thực: Vui lòng đăng nhập để thực hiện thao tác với hệ thống."
            
        system_prompt = f"""SYSTEM IDENTITY: DocLib Core System - API Tool Dispatcher.
OBJECTIVE: Analyze the user intent and select the appropriate system tool for execution.
OUTPUT_LANGUAGE: The JSON values must exactly match the language of the user's input query.

AVAILABLE TOOLS:
{self.tools_prompt}

RULES:
1. You MUST output ONLY a valid JSON object.
2. The JSON object must conform to the following schema:
{{
    "tool": "<tool_name_or_none>",
    "params": {{
        "<param_1>": "<value_1>"
    }}
}}
3. If no tools match the user's request, set "tool" to "none" and "params" to {{}}.
4. Do NOT output any explanatory text outside the JSON object.

<example>
<user_input>Create a folder called AI Research</user_input>
<output>
{{
    "tool": "create_directory",
    "params": {{
        "name": "AI Research"
    }}
}}
</output>
</example>"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=action)
            ]
            res = await llm.ainvoke(messages)
            content = res.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            try:
                decision = json.loads(content)
            except Exception as e:
                logger.error(f"InternalAPI JSON parse failed. Content: {content}. Error: {e}")
                return "Hệ thống không thể nhận diện được yêu cầu thao tác. Vui lòng kiểm tra lại câu lệnh."
                
            tool_name = decision.get("tool")
            tool_params = decision.get("params", {})
            
            if tool_name == "none" or tool_name not in self.tool_map:
                return f"Từ chối thực thi: Hệ thống không có công cụ nào phù hợp để xử lý yêu cầu này."
                
            logger.info(f"InternalAPI: Invoking tool '{tool_name}' with params {tool_params}")
            selected_tool = self.tool_map[tool_name]
            
            try:
                tool_result = await selected_tool.ainvoke(tool_params)
                return str(tool_result)
            except Exception as e:
                logger.error(f"InternalAPI: Tool '{tool_name}' failed: {e}")
                return f"Đã xảy ra lỗi khi thực thi thao tác: {str(e)}"
                
        except Exception as e:
            logger.error(f"InternalAPI: Task execution failed: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

internal_api_agent = InternalAPIAgent()
