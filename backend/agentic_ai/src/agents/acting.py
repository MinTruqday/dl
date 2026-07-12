from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from loguru import logger
from src.core.registry import PromptType, registry
from src.tools.interface import llm, tools

from src.core.infrastructure.configuration import settings

_MAX_ATTEMPTS = 3

# Tools that require explicit user approval before execution
_REQUIRES_APPROVAL_TOOLS = frozenset({
    "delete_document",
    "restore_document",
    "create_document",
    "send_virtual_tip",
    "redeem_coupon",
})


def _is_validation_error(exc: Exception) -> bool:
    return (
        "validation error" in str(exc).lower()
        or "validation" in str(type(exc)).lower()
    )


def _is_transient_error(exc: Exception) -> bool:
    s = str(exc)
    return any(code in s for code in ("504", "503", "500")) or "timeout" in s.lower()


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
        self, action: str, params: dict, user_id: str, token: str = None, auto_approve: bool = False
    ) -> str:
        if not token and action != "public_query":
            return "Bạn cần phải xác thực danh tính để tiếp tục thực hiện thao tác này"

        system_prompt = registry.get(PromptType.TOOL_DISPATCHER)

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=action),
            ]

            llm_with_tools = llm.bind_tools(tools)
            is_last = lambda attempt: attempt == _MAX_ATTEMPTS - 1

            for attempt in range(_MAX_ATTEMPTS):
                try:
                    res = await llm_with_tools.ainvoke(messages)
                except Exception as e:
                    if _is_validation_error(e):
                        logger.warning(f"LLM output validation error (attempt {attempt+1}): {e}")
                        messages.append(HumanMessage(
                            content=(
                                f"Your previous response failed validation: {e}. "
                                "This often happens if you pass a JSON list `[...]` instead of a JSON object `{...}` for tool arguments. "
                                "YOU MUST generate a valid JSON dictionary for the tool arguments."
                            )
                        ))
                        if is_last(attempt):
                            return "Đã xảy ra lỗi trong quá trình xử lý, vui lòng thử lại sau giây lát"
                        continue
                    raise

                invalid_calls = getattr(res, "invalid_tool_calls", [])
                if invalid_calls:
                    logger.warning(f"LLM produced invalid tool calls (attempt {attempt+1}): {invalid_calls}")
                    messages.append(HumanMessage(
                        content=(
                            f"Your tool calls were invalid: {invalid_calls}. "
                            "This often happens if you pass a JSON list instead of a JSON object for tool arguments. "
                            "YOU MUST generate a valid JSON dictionary for the tool arguments."
                        )
                    ))
                    if is_last(attempt):
                        return "Đã xảy ra lỗi trong quá trình xử lý, vui lòng thử lại sau giây lát"
                    continue

                if not res.tool_calls:
                    logger.warning(f"LLM failed to call a tool (attempt {attempt+1}). Response: {res.content}")
                    messages.append(HumanMessage(
                        content="You did not call any tools. You MUST respond by invoking exactly ONE tool from the provided list. Do not respond with plain text."
                    ))
                    if is_last(attempt):
                        return "Hệ thống không tìm thấy công cụ phù hợp để xử lý yêu cầu của bạn"
                    continue

                tool_call = res.tool_calls[0]
                tool_name = tool_call["name"]
                tool_params = tool_call["args"]

                if tool_name not in self.tool_map:
                    return "Công cụ bạn yêu cầu hiện không khả dụng hoặc không tồn tại trên hệ thống"

                if tool_name in _REQUIRES_APPROVAL_TOOLS and not auto_approve:
                    return "Thao tác này yêu cầu xác nhận ủy quyền trực tiếp từ bạn"

                # ── Step 4: Execute the tool ──────────────────────────────────
                logger.info("Initializing utility")
                selected_tool = self.tool_map[tool_name]
                try:
                    tool_result = await selected_tool.ainvoke(
                        tool_params, config={"configurable": {"token": token, "user_id": state.get("user_id")}}
                    )
                    return str(tool_result)
                except Exception as e:
                    messages.append(res)
                    messages.append(ToolMessage(
                        content="The system encountered an error while executing the utility and requests a verification of the input data",
                        tool_call_id=tool_call["id"],
                    ))
                    logger.exception("Data processing issue encountered, system is automatically retrying")
                    if is_last(attempt):
                        return "Thao tác thực hiện không hoàn tất sau nhiều lần thử lại, vui lòng kiểm tra lại yêu cầu"

        except Exception as e:
            logger.exception("Execution process interrupted")
            return f"Đã xảy ra lỗi trong quá trình xử lý, vui lòng thử lại sau giây lát {e}"


actor = ActingAgent()
