from core.config import settings
from huggingface_hub import AsyncInferenceClient
from langchain_core.prompts import PromptTemplate
from loguru import logger
from pydantic import BaseModel, Field
from typing import Literal
from src.core.prompt_registry import PromptType, prompt_registry
from src.utils.hf import HFInferenceChat

class RouteDecision(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning")
    route: Literal["action", "knowledge", "chat"] = Field(description="The chosen route: 'action', 'knowledge', or 'chat'")
    answer: str = Field(default="", description="Direct response if route is 'chat', else empty string")

class SemanticRouter:
    def __init__(self):
        llama_model = settings.LLAMA_MODEL
        if not llama_model:
            raise ValueError("The language model configuration is currently missing from the system settings")

        self.llama_client = AsyncInferenceClient(
            model=settings.LLAMA_MODEL,
            token=settings.HF_TOKEN,
        )
        self.router_llm = HFInferenceChat(
            client=self.llama_client, model=settings.LLAMA_MODEL
        )

    async def execute(self, query: str) -> dict:
        prompt = PromptTemplate(
            template=prompt_registry.get(PromptType.PRIMARY_ROUTER),
            input_variables=["question"],
        )
        try:
            structured_llm = self.router_llm.with_structured_output(RouteDecision)
            res: RouteDecision = await structured_llm.ainvoke(prompt.format(question=query))
            
            route = res.route.lower()
            if route not in ["chat", "action", "knowledge"]:
                route = "knowledge"

            return {"route": route, "answer": res.answer}

        except Exception:
            logger.exception("The semantic routing process failed due to an unexpected system exception")
            return {"route": "knowledge", "answer": ""}

semantic_router = SemanticRouter()