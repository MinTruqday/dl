import json

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from src.core.registry import PromptType, registry
from src.agents.planning import llm
from src.harness.agentops import agentops
from src.harness.tool import ToolHarness
from src.tools import tools

from src.core.infrastructure.configuration import settings

_MAX_ATTEMPTS = 3

_REQUIRES_APPROVAL_TOOLS = frozenset(
    {
        "create_document",
        "delete_document",
        "edit_document_block",
        "edit_document_text",
        "manage_user_instructions",
        "propose_document_edits",
        "replace_document_content",
        "restore_document",
        "update_document_metadata",
        "execute_mcp_tool",
    }
)

_AUTO_SAFE_TOOLS = frozenset(
    {
        "create_document",
        "edit_document_block",
        "edit_document_text",
        "propose_document_edits",
        "update_document_metadata",
    }
)


def _is_validation_error(exc: Exception) -> bool:
    return "validation error" in str(exc).lower() or "validation" in str(type(exc)).lower()


class ActingAgent:
    """
    <module_purpose>
    DocLib Acting Agent for executing registered tools based on LLM decisions.
    </module_purpose>
    <contract>
    - Precondition: Tool name and validated arguments. User authentication for sensitive tools.
    - Postcondition: Executes the tool and returns the result string.
    - Error Handling: Handles exceptions locally and communicates failures contextually.
    </contract>
    """

    def __init__(self):
        self.base_url = settings.INTERNAL_API_URL
        self.tool_map = {t.name: t for t in tools}
        self.tool_harness = ToolHarness()
        for registered_tool in tools:
            self.tool_harness.register(
                registered_tool.name,
                registered_tool.ainvoke,
                max_retries=(
                    0 if registered_tool.name in _REQUIRES_APPROVAL_TOOLS else 2
                ),
            )

        tool_descriptions = []
        for t in tools:
            args = ""
            if hasattr(t, "args_schema") and t.args_schema:
                schema = t.args_schema.model_json_schema()
                props = schema.get("properties", {})
                args = ", ".join([f"{k} type {v.get('type')}" for k, v in props.items()])
            tool_descriptions.append(f"- {t.name}({args}) {t.description}")
        self.tools_prompt = "\n".join(tool_descriptions)

    async def execute(
        self,
        action: str,
        params: dict,
        user_id: str,
        token: str = None,
        auto_approve: bool = False,
        approval_policy: str = "manual",
        session_id: str = "",
        approval_id: str = None,
        ai_tier: str = "BASIC",
    ) -> str:
        if not token and action != "public_query":
            return json.dumps({"status": "authentication_required"})

        system_prompt = registry.get(PromptType.TOOL_DISPATCHER)

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=json.dumps(
                        {"action": action, "supplied_parameters": params},
                        ensure_ascii=False,
                        default=str,
                    )
                ),
            ]

            llm_with_tools = llm.bind_tools(tools)
            is_last = lambda attempt: attempt == _MAX_ATTEMPTS - 1

            for attempt in range(_MAX_ATTEMPTS):
                try:
                    res = await llm_with_tools.ainvoke(messages)
                except Exception as e:
                    if _is_validation_error(e):
                        logger.warning(
                            "Tool selection validation failed attempt={} error_type={}",
                            attempt + 1,
                            type(e).__name__,
                        )
                        messages.append(
                            HumanMessage(
                                content=(
                                    "The previous response failed schema validation. "
                                    "Return exactly one registered tool call with a JSON object for arguments."
                                )
                            )
                        )
                        if is_last(attempt):
                            return json.dumps({"status": "tool_selection_validation_failed"})
                        continue
                    raise

                invalid_calls = getattr(res, "invalid_tool_calls", [])
                if invalid_calls:
                    logger.warning(
                        "Tool selection produced invalid calls attempt={} count={}",
                        attempt + 1,
                        len(invalid_calls),
                    )
                    messages.append(
                        HumanMessage(
                            content=(
                                f"Your tool calls were invalid: {invalid_calls}. "
                                "This often happens if you pass a JSON list instead of a JSON object for tool arguments. "
                                "YOU MUST generate a valid JSON dictionary for the tool arguments."
                            )
                        )
                    )
                    if is_last(attempt):
                        return json.dumps({"status": "tool_selection_validation_failed"})
                    continue

                if not res.tool_calls:
                    logger.warning(
                        "Tool selection returned no call attempt={} response_chars={}",
                        attempt + 1,
                        len(str(res.content)),
                    )
                    return json.dumps({"status": "tool_unavailable"})

                tool_call = res.tool_calls[0]
                tool_name = tool_call["name"]
                tool_params = tool_call["args"]

                if tool_name not in self.tool_map:
                    return json.dumps({"status": "tool_unavailable"})

                selected_tool = self.tool_map[tool_name]
                if tool_name in {
                    "search_mcp_connectors",
                    "suggest_mcp_connectors",
                    "execute_mcp_tool",
                } and str(ai_tier).upper() not in {"PRO", "PREMIUM"}:
                    return json.dumps({"status": "advanced_mode_requires_pro"})
                approved_automatically = auto_approve or (
                    approval_policy == "auto_safe" and tool_name in _AUTO_SAFE_TOOLS
                )
                if tool_name in _REQUIRES_APPROVAL_TOOLS and not approved_automatically:
                    from src.loop.intervention import intervention

                    if approval_id:
                        approved = await intervention.consume_approval(
                            intervention_id=approval_id,
                            session_id=session_id,
                            user_id=str(user_id),
                            action_type=tool_name,
                        )
                        if not approved:
                            return json.dumps(
                                {"status": "approval_invalid", "tool_name": tool_name}
                            )
                    else:
                        approval = await intervention.request_approval(
                            session_id=session_id,
                            user_id=str(user_id),
                            action_type=tool_name,
                            description=selected_tool.description,
                            proposed_action=json.dumps(
                                tool_params, ensure_ascii=False, default=str
                            ),
                            risk_level=(
                                "high"
                                if tool_name
                                in {
                                    "delete_document",
                                    "replace_document_content",
                                    "restore_document",
                                }
                                else "medium"
                            ),
                        )
                        approved = await intervention.wait_for_approval(
                            approval.intervention_id, session_id, str(user_id), tool_name
                        )
                        if not approved:
                            return json.dumps(
                                {"status": "approval_rejected", "tool_name": tool_name}
                            )

                logger.info("Tool execution started tool={}", tool_name)
                tool_result = await self.tool_harness.execute(
                    tool_name,
                    session_id,
                    tool_params,
                    config={"configurable": {"token": token, "user_id": user_id}},
                )
                agentops.record_tool_call(
                    session_id,
                    tool_name,
                    duration_ms=tool_result.duration_ms,
                    success=tool_result.success,
                )
                if tool_result.success:
                    logger.info(
                        "Tool execution completed tool={} output_chars={}",
                        tool_name,
                        len(str(tool_result.data)),
                    )
                    return str(tool_result.data)
                logger.error(
                    "Tool execution failed tool={} attempts={}",
                    tool_name,
                    tool_result.attempt,
                )
                return json.dumps(
                    {
                        "status": "tool_execution_failed",
                        "tool_name": tool_name,
                        "attempts": tool_result.attempt,
                    }
                )

        except Exception:
            logger.exception("Execution process interrupted")
            return json.dumps({"status": "action_execution_failed"})


actor = ActingAgent()
