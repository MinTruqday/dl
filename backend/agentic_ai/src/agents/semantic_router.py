from core.config import settings
from huggingface_hub import AsyncInferenceClient
from langchain_core.prompts import PromptTemplate
from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry
from src.utils.hf import HFInferenceChat


class SemanticRouter:
    def __init__(self):
        llama_model = settings.LLAMA_MODEL
        if not llama_model:
            raise ValueError("The primary language model configuration is currently missing from the system settings")

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
            from pydantic import BaseModel, Field
            from src.agents.planning import llm

            class RouteDecision(BaseModel):
                reasoning: str = Field(description="Step-by-step reasoning")
                route: str = Field(
                    description="The chosen route: 'action', 'knowledge', or 'chat'"
                )
                answer: str = Field(
                    description="Direct response if route is 'chat', else empty string"
                )

            try:
                structured_llm = llm.with_structured_output(RouteDecision)
                res = await structured_llm.ainvoke(prompt.format(question=query))
                route = res.route.lower()
                answer = res.answer
            except Exception:
                import json
                import re

                raw_res = await llm.ainvoke(prompt.format(question=query))
                match = re.search(r"\{.*\}", raw_res.content, re.DOTALL)
                if match:
                    decision = json.loads(match.group(0))
                else:
                    decision = {}
                route = decision.get("route", "knowledge").lower()
                answer = decision.get("answer", "")

            if route not in ["chat", "action", "knowledge"]:
                route = "knowledge"

            logger.info("The system has successfully categorized the user request and selected the appropriate execution route")
            return {"route": route, "answer": answer}

        except Exception:
            logger.error("The semantic routing process failed due to an unexpected system exception")
            return {"route": "knowledge", "answer": ""}


semantic_router = SemanticRouter()