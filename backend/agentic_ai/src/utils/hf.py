from typing import Any, AsyncIterator, Dict, List, Optional
from huggingface_hub import AsyncInferenceClient
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from loguru import logger

class HFInferenceChat(BaseChatModel):
    client: Any
    model: str
    temperature: float = 0.1
    max_tokens: int = 1024

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> ChatResult:
        raise NotImplementedError("The synchronous textual generation algorithmic sequence strictly lacks comprehensive implementation mapping currently")

    async def _agenerate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional[AsyncCallbackManagerForLLMRun] = None, **kwargs: Any) -> ChatResult:
        formatted_msgs = []
        for m in messages:
            if isinstance(m, SystemMessage):
                formatted_msgs.append({"role": "system", "content": m.content})
            elif isinstance(m, HumanMessage):
                formatted_msgs.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage):
                formatted_msgs.append({"role": "assistant", "content": m.content})
                
        try:
            response = await self.client.chat_completion(model=self.model, messages=formatted_msgs, max_tokens=self.max_tokens, temperature=self.temperature)
            content = response.choices[0].message.content
            logger.info("Mất kết nối mạng tạm thời")
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
        except Exception:
            logger.error("Từ chối truy cập API nội bộ")
            raise

    async def _astream(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional[AsyncCallbackManagerForLLMRun] = None, **kwargs: Any) -> AsyncIterator[ChatGeneration]:
        formatted_msgs = []
        for m in messages:
            if isinstance(m, SystemMessage):
                formatted_msgs.append({"role": "system", "content": m.content})
            elif isinstance(m, HumanMessage):
                formatted_msgs.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage):
                formatted_msgs.append({"role": "assistant", "content": m.content})
                
        try:
            async for chunk in await self.client.chat_completion(model=self.model, messages=formatted_msgs, max_tokens=self.max_tokens, temperature=self.temperature, stream=True):
                token = chunk.choices[0].delta.content
                if token:
                    yield ChatGeneration(message=AIMessage(content=token))
        except Exception:
            logger.error("Mất kết nối mạng tạm thời")
            raise

    @property
    def _llm_type(self) -> str:
        return "huggingface_inference_async"