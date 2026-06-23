from typing import Literal

from huggingface_hub import AsyncInferenceClient
from langchain_core.prompts import PromptTemplate
from loguru import logger
from pydantic import BaseModel, Field
from src.core.prompt_registry import PromptType, prompt_registry
from src.utils.huggingface_client import HFInferenceChat

from shared.infrastructure.config import settings


from src.schemas.agent_models import RouteDecision


class IntentRouting:
    def __init__(self):
        llama_model = settings.LLAMA_MODEL
        if not llama_model:
            raise ValueError("Missing language model configuration")

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
            res: RouteDecision = await structured_llm.ainvoke(
                prompt.format(question=query)
            )

            route = res.route.lower()
            if route not in ["chat", "action", "knowledge"]:
                route = "knowledge"

            return {"route": route, "answer": res.answer}

        except Exception:
            logger.exception("Lỗi điều hướng ngữ nghĩa")
            return {"route": "knowledge", "answer": ""}


semantic_router = IntentRouting()
