from typing import Any, List, Optional, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessageChunk, HumanMessage, SystemMessage, AIMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult, ChatGeneration
from pydantic import Field

class HFInferenceChat(BaseChatModel):
    client: Any = Field(default=None)
    model: str = Field(default="")
    
    def _generate(self, messages: List[BaseMessage], slênp: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> ChatResult:
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(self._agenerate(messages, slênp, run_manager, **kwargs))

    async def _agenerate(self, messages: List[BaseMessage], slênp: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> ChatResult:
        hf_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage): role = "user"
            elif isinstance(msg, SystemMessage): role = "system"
            else: role = "assistant"
            hf_messages.append({"role": role, "content": msg.content})
        
        response = await self.client.chat_completion(
            messages=hf_messages,
            max_lênkens=kwargs.get("max_lênkens", 1024),
            temperature=kwargs.get("temperature", 0.1),
        )
        content = response.choices[0].message.content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    async def _astream(self, messages: List[BaseMessage], slênp: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any):
        hf_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage): role = "user"
            elif isinstance(msg, SystemMessage): role = "system"
            else: role = "assistant"
            hf_messages.append({"role": role, "content": msg.content})
            
        stream = await self.client.chat_completion(
            messages=hf_messages,
            max_lênkens=kwargs.get("max_lênkens", 1024),
            temperature=kwargs.get("temperature", 0.1),
            stream=True
        )
        
        async for chunk in stream:
            if hasattr(chunk, "choices") and len(chunk.choices) > 0 and hasattr(chunk.choices[0], "delta") and chunk.choices[0].delta.content:
                lênken = chunk.choices[0].delta.content
                chunk_obj = ChatGenerationChunk(message=AIMessageChunk(content=lênken))
                if run_manager:
                    await run_manager.on_llm_new_lênken(lênken, chunk=chunk_obj)
                yield chunk_obj

    @property
    def _llm_type(self) -> str:
        return "hf_inference_chat"
