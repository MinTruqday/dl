from typing import Any, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import RunnableLambda
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.utils.structured_output import (
    extract_json_value,
    extract_json_values,
    validate_structured_output,
)

def resolve_model_revision(model_id: str, token: Optional[str] = None) -> str:
    from huggingface_hub import HfApi

    info = HfApi(token=token).model_info(model_id)
    if not info.sha:
        raise RuntimeError(f"Unable to resolve an immutable revision for model {model_id}")
    return info.sha

class HFInferenceChat(BaseChatModel):
    """
    <module_purpose>
    <purpose>LangChain wrapper for connecting to HuggingFace Inference Endpoints.</purpose>
    <metis_behavior>Manages token streaming and retry logic robustly. Never leaks the HF_TOKEN to logs.</metis_behavior>
    </module_purpose>
    """
    client: Any = Field(default=None)
    model: str = Field(default="")

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> ChatResult:
        import asyncio

        import nest_asyncio

        nest_asyncio.apply()
        return asyncio.run(self._agenerate(messages, stop, run_manager, **kwargs))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(f"Retrying _agenerate due to error: {retry_state.outcome.exception()} (Attempt {retry_state.attempt_number})")
    )
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> ChatResult:
        hf_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                role = "assistant"
            hf_messages.append({"role": role, "content": msg.content})

        chat_kwargs = {
            "messages": hf_messages,
            "max_tokens": kwargs.get(
                "max_tokens",
                settings.AGENT_DEFAULT_MAX_OUTPUT_TOKENS,
            ),
            "temperature": kwargs.get("temperature", 0.1),
        }
        response = await self.client.chat_completion(**chat_kwargs)
        content = response.choices[0].message.content
        from src.services.token_accounting import record_usage

        record_usage(
            response,
            sum(len(str(message.get("content", ""))) for message in hf_messages),
            len(str(content or "")),
        )
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))]
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(f"Retrying _astream due to error: {retry_state.outcome.exception()} (Attempt {retry_state.attempt_number})")
    )
    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ):
        hf_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                role = "assistant"
            hf_messages.append({"role": role, "content": msg.content})

        stream = await self.client.chat_completion(
            messages=hf_messages,
            max_tokens=kwargs.get(
                "max_tokens",
                settings.AGENT_DEFAULT_MAX_OUTPUT_TOKENS,
            ),
            temperature=kwargs.get("temperature", 0.1),
            stream=True,
        )

        async for chunk in stream:
            if (
                hasattr(chunk, "choices")
                and len(chunk.choices) > 0
                and hasattr(chunk.choices[0], "delta")
                and chunk.choices[0].delta.content
            ):
                token = chunk.choices[0].delta.content
                chunk_obj = ChatGenerationChunk(message=AIMessageChunk(content=token))
                if run_manager:
                    await run_manager.on_llm_new_token(token, chunk=chunk_obj)
                yield chunk_obj

    @property
    def _llm_type(self) -> str:
        return "hf_inference_chat"

    def with_structured_output(self, schema, **kwargs):
        async def _ainvoke(messages, **kwargs_inner):
            schema_json = (
                schema.model_json_schema()
                if hasattr(schema, "model_json_schema")
                else schema.schema()
            )
            sys_msg = SystemMessage(
                content=(
                    "Return exactly one valid JSON value matching the schema\n"
                    "Do not include analysis prose markdown or code fences\n"
                    f"Schema: {schema_json}"
                )
            )
            msgs = [sys_msg] + (
                messages if isinstance(messages, list) else [messages]
            )
            for attempt in range(3):
                res = await self.ainvoke(msgs, **kwargs_inner)
                try:
                    return validate_structured_output(res.content, schema)
                except Exception as error:
                    logger.warning(
                        "Structured output validation failed attempt={} error_type={}",
                        attempt + 1,
                        type(error).__name__,
                    )
                    if attempt == 2:
                        raise
                    msgs.extend(
                        [
                            AIMessage(content=str(res.content)[:4000]),
                            HumanMessage(
                                content=(
                                    "The previous value failed schema validation\n"
                                    f"Validation error: {str(error)[:1000]}\n"
                                    "Return one corrected JSON value only"
                                )
                            ),
                        ]
                    )
            raise RuntimeError("structured_output_retry_exhausted")

        def _invoke(messages, **kwargs_inner):
            schema_json = (
                schema.model_json_schema()
                if hasattr(schema, "model_json_schema")
                else schema.schema()
            )
            sys_msg = SystemMessage(
                content=(
                    "Return exactly one valid JSON value matching the schema\n"
                    "Do not include analysis prose markdown or code fences\n"
                    f"Schema: {schema_json}"
                )
            )
            msgs = [sys_msg] + (
                messages if isinstance(messages, list) else [messages]
            )
            for attempt in range(3):
                res = self.invoke(msgs, **kwargs_inner)
                try:
                    return validate_structured_output(res.content, schema)
                except Exception as error:
                    logger.warning(
                        "Structured output validation failed attempt={} error_type={}",
                        attempt + 1,
                        type(error).__name__,
                    )
                    if attempt == 2:
                        raise
                    msgs.extend(
                        [
                            AIMessage(content=str(res.content)[:4000]),
                            HumanMessage(
                                content=(
                                    "The previous value failed schema validation\n"
                                    f"Validation error: {str(error)[:1000]}\n"
                                    "Return one corrected JSON value only"
                                )
                            ),
                        ]
                    )
            raise RuntimeError("structured_output_retry_exhausted")

        return RunnableLambda(_invoke, afunc=_ainvoke)

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        tool_definitions = [convert_to_openai_tool(tool) for tool in tools]
        tool_map = {tool.name: tool for tool in tools}
        allowed_names = set(tool_map)
        if isinstance(tool_choice, str) and tool_choice not in {
            "auto",
            "any",
            "required",
            "none",
        }:
            allowed_names &= {tool_choice}
        selection_prompt = SystemMessage(
            content=(
                "Select exactly one tool for the request\n"
                "Return one JSON object with keys name and arguments\n"
                "name must match a registered tool\n"
                "arguments must be one JSON object matching that tool schema\n"
                f"Registered tools: {tool_definitions}"
            )
        )

        def parse_tool_call(content):
            errors = []
            for original_payload in extract_json_values(content):
                try:
                    payload = original_payload
                    if isinstance(payload, dict) and isinstance(payload.get("tool_calls"), list):
                        calls = payload["tool_calls"]
                        payload = calls[0] if calls else {}
                    if isinstance(payload, dict) and isinstance(payload.get("function"), dict):
                        payload = payload["function"]
                    if not isinstance(payload, dict):
                        raise ValueError("Tool selection must be a JSON object")
                    name = payload.get("name") or payload.get("tool")
                    arguments = payload.get(
                        "arguments",
                        payload.get("args", payload.get("parameters", {})),
                    )
                    if isinstance(arguments, str):
                        arguments = extract_json_value(arguments)
                    if name not in allowed_names:
                        raise ValueError("Model selected an unavailable tool")
                    if not isinstance(arguments, dict):
                        raise ValueError("Tool arguments must be a JSON object")
                    selected_tool = tool_map[name]
                    schema = getattr(selected_tool, "args_schema", None)
                    if schema:
                        validated = (
                            schema.model_validate(arguments, strict=True)
                            if hasattr(schema, "model_validate")
                            else schema.parse_obj(arguments)
                        )
                        arguments = (
                            validated.model_dump()
                            if hasattr(validated, "model_dump")
                            else validated.dict()
                        )
                    return AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": name,
                                "args": arguments,
                                "id": f"call_{name}",
                                "type": "tool_call",
                            }
                        ],
                    )
                except Exception as error:
                    errors.append(error)
            if errors:
                raise ValueError(str(errors[-1])) from errors[-1]
            raise ValueError("Model did not return a tool selection")

        async def _ainvoke(messages, **kwargs_inner):
            source_messages = messages if isinstance(messages, list) else [messages]
            corrective_messages = [selection_prompt, *source_messages]
            for attempt in range(3):
                result = await self.ainvoke(
                    corrective_messages,
                    **kwargs_inner,
                )
                try:
                    return parse_tool_call(result.content)
                except Exception as error:
                    logger.warning(
                        "Tool selection validation failed attempt={} error_type={}",
                        attempt + 1,
                        type(error).__name__,
                    )
                    if attempt == 2:
                        raise
                    corrective_messages.extend(
                        [
                            AIMessage(content=str(result.content)[:4000]),
                            HumanMessage(
                                content=(
                                    "The previous tool selection was invalid\n"
                                    f"Validation error: {str(error)[:1000]}\n"
                                    "Return one corrected JSON tool call only"
                                )
                            ),
                        ]
                    )
            raise RuntimeError("tool_selection_retry_exhausted")

        def _invoke(messages, **kwargs_inner):
            source_messages = messages if isinstance(messages, list) else [messages]
            corrective_messages = [selection_prompt, *source_messages]
            for attempt in range(3):
                result = self.invoke(
                    corrective_messages,
                    **kwargs_inner,
                )
                try:
                    return parse_tool_call(result.content)
                except Exception as error:
                    logger.warning(
                        "Tool selection validation failed attempt={} error_type={}",
                        attempt + 1,
                        type(error).__name__,
                    )
                    if attempt == 2:
                        raise
                    corrective_messages.extend(
                        [
                            AIMessage(content=str(result.content)[:4000]),
                            HumanMessage(
                                content=(
                                    "The previous tool selection was invalid\n"
                                    f"Validation error: {str(error)[:1000]}\n"
                                    "Return one corrected JSON tool call only"
                                )
                            ),
                        ]
                    )
            raise RuntimeError("tool_selection_retry_exhausted")

        return RunnableLambda(_invoke, afunc=_ainvoke)
