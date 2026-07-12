from typing import Literal

from huggingface_hub import AsyncInferenceClient
from langchain_core.prompts import PromptTemplate
from loguru import logger
from pydantic import BaseModel, Field
from src.core.registry import PromptType, registry
from src.utils.huggingface import HFInferenceChat

from src.core.infrastructure.configuration import settings

from src.schemas.routing import RouteDecision

class RouteAgent:
    def __init__(self):
        llama_model = settings.LLM_MODEL
        if not llama_model:
            raise ValueError("System is not fully configured for the AI language model")

        self.llama_client = AsyncInferenceClient(
            model=settings.LLM_MODEL,
            token=settings.HF_TOKEN,
        )
        self.router_llm = HFInferenceChat(
            client=self.llama_client, model=settings.LLM_MODEL
        )

    async def execute(self, query: str) -> dict:
        prompt = PromptTemplate(
            template=registry.get(PromptType.PRIMARY_ROUTER),
            input_variables=["question"],
        )
        try:
            structured_llm = self.router_llm.with_structured_output(RouteDecision)
            res: RouteDecision = await structured_llm.ainvoke(
                prompt.format(question=query)
            )

            route = res.route.lower()
            if route not in ["chat", "action", "knowledge"]:
                route = "knowledge"

            return {"route": route, "answer": res.answer}

        except Exception as e:
            logger.exception("Semantic routing error")
            return {"route": "knowledge", "answer": ""}

semantic_router = RouteAgent()
