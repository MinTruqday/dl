import json

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from src.core.registry import PromptType, registry
from src.agents.react.planning import llm
from src.harness.agentops import agentops
from src.harness.tool import ToolHarness
from src.tools import tools

from src.core.infrastructure.configuration import settings

_MAX_ATTEMPTS = 3

_REQUIRES_APPROVAL_TOOLS = frozenset(
    {
        "delete_document",
        "manage_user_instructions",
        "restore_document",
        "update_document_metadata",
        "create_test_case_draft",
        "create_trace_link_suggestion",
        "create_impact_analysis",
        "create_maintenance_proposal",
        "create_regression_recommendation",
        "apply_test_case_revision",
        "confirm_trace_link",
        "baseline_requirement_version",
        "approve_test_case_version",
        "mark_test_case_obsolete",
    }
)

_HUMAN_ONLY_APPROVAL_TOOLS = frozenset({"apply_test_case_revision", "confirm_trace_link", "baseline_requirement_version", "approve_test_case_version", "mark_test_case_obsolete"})

_AUTO_SAFE_TOOLS = frozenset({"update_document_metadata"})


def _is_validation_error(exc: Exception) -> bool:
    return "validation error" in str(exc).lower() or "validation" in str(type(exc)).lower()


def _can_approve_automatically(tool_name: str, auto_approve: bool, approval_policy: str) -> bool:
    return tool_name not in _HUMAN_ONLY_APPROVAL_TOOLS and (
        auto_approve or (approval_policy == "auto_safe" and tool_name in _AUTO_SAFE_TOOLS)
    )


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
                max_retries=(0 if registered_tool.name in _REQUIRES_APPROVAL_TOOLS else 2),
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

    def _candidate_tools(self, action: str):
        normalized = action.casefold()
        intent_tools = {
            "read_document": ("read_document", "đọc tài liệu"),
            "get_my_documents": ("get_my_documents", "tài liệu của tôi"),
            "delete_document": ("delete_document", "xóa tài liệu"),
            "restore_document": ("restore_document", "khôi phục tài liệu"),
        }
        names = {
            tool_name
            for tool_name, markers in intent_tools.items()
            if any(marker in normalized for marker in markers)
        }
        return [tool for tool in tools if tool.name in names] or tools

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

            candidate_tools = self._candidate_tools(action)
            forced_tool = candidate_tools[0].name if len(candidate_tools) == 1 else None
            llm_with_tools = llm.bind_tools(candidate_tools, tool_choice=forced_tool)
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
                approved_automatically = _can_approve_automatically(
                    tool_name, auto_approve, approval_policy
                )
                risk_level = (
                    "high" if tool_name in {"delete_document", "restore_document"} else "medium"
                )
                if tool_name in _REQUIRES_APPROVAL_TOOLS:
                    from src.loop.intervention import intervention

                    if tool_name not in _HUMAN_ONLY_APPROVAL_TOOLS:
                        approved_automatically = (
                            approved_automatically
                            or intervention.has_session_grant(
                                session_id, str(user_id), tool_name, risk_level
                            )
                        )
                if tool_name in _REQUIRES_APPROVAL_TOOLS and not approved_automatically:
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
                            risk_level=risk_level,
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
                    config={
                        "configurable": {
                            "token": (
                                token if str(token).startswith("Bearer ") else f"Bearer {token}"
                            ),
                            "user_id": user_id,
                        }
                    },
                )
                agentops.record_tool_call(
                    session_id,
                    tool_name,
                    duration_ms=tool_result.duration_ms,
                    success=tool_result.success,
                )
                if tool_result.success:
                    semantic_data = tool_result.data
                    if isinstance(semantic_data, str):
                        parsed_semantic_data = semantic_data
                        for _ in range(4):
                            if not isinstance(parsed_semantic_data, str):
                                break
                            try:
                                parsed_semantic_data = json.loads(parsed_semantic_data)
                            except json.JSONDecodeError:
                                if '\\"' not in parsed_semantic_data:
                                    break
                                try:
                                    parsed_semantic_data = json.loads(f'"{parsed_semantic_data}"')
                                except json.JSONDecodeError:
                                    break
                        if isinstance(parsed_semantic_data, dict) and parsed_semantic_data.get(
                            "status"
                        ) not in {None, "success", "completed"}:
                            logger.warning(
                                "Tool returned business failure tool={} status={}",
                                tool_name,
                                parsed_semantic_data.get("status"),
                            )
                            return json.dumps(parsed_semantic_data, ensure_ascii=False, default=str)
                        if parsed_semantic_data is not semantic_data:
                            semantic_data = parsed_semantic_data
                    logger.info(
                        "Tool execution completed tool={} output_chars={}",
                        tool_name,
                        len(str(tool_result.data)),
                    )
                    return json.dumps(semantic_data, ensure_ascii=False, default=str)
                logger.error(
                    "Tool execution failed tool={} attempts={}", tool_name, tool_result.attempt
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
