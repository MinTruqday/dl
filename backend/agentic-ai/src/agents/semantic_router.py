from loguru import logger
from langchain_core.prompts import PromptTemplate
from core.config import settings
from huggingface_hub import AsyncInferenceClient
from src.utils.hf import HFInferenceChat
from src.core.prompt_registry import prompt_registry, PromptType


class SemanticRouter:
    def __init__(self):
        llama_model = settings.LLAMA_MODEL
        if not llama_model:
            raise ValueError("Chưa cấu hình biến LLAMA_MODEL")
            
        self.llama_client = AsyncInferenceClient(
            model=settings.LLAMA_MODEL,
            token=settings.HF_TOKEN,
        )
        self.router_llm = HFInferenceChat(client=self.llama_client, model=settings.LLAMA_MODEL)

    async def execute(self, query: str) -> dict:
        prompt = PromptTemplate(
            template=prompt_registry.get(PromptType.PRIMARY_ROUTER),
            input_variables=["question"]
        )
        try:
            from src.agents.planning import llm
            from pydantic import BaseModel, Field
            
            class RouteDecision(BaseModel):
                reasoning: str = Field(description="Step-by-step reasoning")
                route: str = Field(description="The chosen route: 'action', 'knowledge', or 'chat'")
                answer: str = Field(description="Direct response if route is 'chat', else empty string")
            
            try:
                structured_llm = llm.with_structured_output(RouteDecision)
                res = await structured_llm.ainvoke(prompt.format(question=query))
                route = res.route.lower()
                answer = res.answer
            except Exception:
                import json
                import re
                raw_res = await llm.ainvoke(prompt.format(question=query))
                match = re.search(r'\{.*\}', raw_res.content, re.DOTALL)
                if match:
                    decision = json.loads(match.group(0))
                else:
                    decision = {}
                route = decision.get("route", "knowledge").lower()
                answer = decision.get("answer", "")
            
            if route not in ["chat", "action", "knowledge"]:
                route = "knowledge"
                
            logger.info("Đã phân loại yêu cầu vào luồng '{route}'")
            return {"route": route, "answer": answer}
            
        except Exception as e:
            logger.error("Điều hướng yêu cầu thất bại do lỗi")
            return {"route": "knowledge", "answer": ""}

semantic_router = SemanticRouter()
