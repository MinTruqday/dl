from typing import Any, Dict, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger

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
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.1),
        }
        if "response_format" in kwargs:
            chat_kwargs["response_format"] = kwargs["response_format"]

        response = await self.client.chat_completion(**chat_kwargs)
        content = response.choices[0].message.content
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
            max_tokens=kwargs.get("max_tokens", 512),
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
        from langchain_core.runnables import RunnableLambda
        import json
        
        def extract_and_parse(text: str):
            try:
                # Handle cases where model wraps JSON in markdown blocks
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                data = json.loads(text.strip())
                return schema(**data)
            except Exception as e:
                # Raise so tenacity can retry
                raise ValueError(f"Failed to parse structured output: {e}. Raw text: {text}")
                
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(Exception),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(f"Retrying _ainvoke structured output due to error: {retry_state.outcome.exception()} (Attempt {retry_state.attempt_number})")
        )
        async def _ainvoke(messages, **kwargs_inner):
            schema_json = schema.schema_json()
            sys_msg = SystemMessage(content=f"Output ONLY valid JSON matching this schema: {schema_json}")
            msgs = [sys_msg] + (messages if isinstance(messages, list) else [messages])
            
            kwargs_inner["response_format"] = {"type": "json_object"}
            
            res = await self.ainvoke(msgs, **kwargs_inner)
            return extract_and_parse(res.content)
            
        def _invoke(messages, **kwargs_inner):
            schema_json = schema.schema_json()
            sys_msg = SystemMessage(content=f"Output ONLY valid JSON matching this schema: {schema_json}")
            msgs = [sys_msg] + (messages if isinstance(messages, list) else [messages])
            kwargs_inner["response_format"] = {"type": "json_object"}
            res = self.invoke(msgs, **kwargs_inner)
            return extract_and_parse(res.content)
            
        runnable = RunnableLambda(_invoke)
        runnable.ainvoke = _ainvoke
        return runnable
