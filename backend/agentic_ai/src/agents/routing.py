import asyncio
from typing import Dict, List, Optional

import numpy as np
from huggingface_hub import AsyncInferenceClient
from langchain_core.prompts import PromptTemplate
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.registry import PromptType, registry
from src.schemas.routing import RouteDecision
from src.utils.huggingface import HFInferenceChat


VALID_AGENTS = {
    "InterpreterAgent": "Executes Python code, runs scripts, performs mathematical calculations and data analysis",
    "EngineAgent": "Searches the internet for real-time information, news, current events and external data",
    "Action": "Performs file operations, editing, writing, and complex multi-tool tasks within the DocLib system",
    "Knowledge": "Retrieves information from the local document library using semantic vector search",
    "Reasoning": "Performs deep logical analysis, reasoning, evaluation, and multi-step problem solving",
    "SwarmAgent": "Writes, reviews, and secures complex software code using a multi-agent team",
    "MCTSAgent": "Solves complex logic problems by exploring multiple solution branches via Monte Carlo Tree Search",
}


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    va = np.array(a)
    vb = np.array(b)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


class SemanticRouterValidator:
    """
    <module_purpose>
    <purpose>Validates and corrects agent names produced by the Planner using vector similarity as a safety net.</purpose>
    <metis_behavior>Computes cosine similarity between task embedding and pre-cached agent description embeddings. Corrects invalid agent names silently without breaking the pipeline.</metis_behavior>
    </module_purpose>
    """

    def __init__(self):
        self._agent_embeddings: Optional[Dict[str, List[float]]] = None

    def _get_embedder(self):
        from src.rag.embedding import embedder
        return embedder

    def _compute_agent_embeddings(self) -> Dict[str, List[float]]:
        embedder = self._get_embedder()
        result = {}
        for agent_name, description in VALID_AGENTS.items():
            try:
                vec = embedder.embed_query(description)
                result[agent_name] = vec
            except Exception:
                logger.exception(f"Failed to embed agent description for {agent_name}")
        logger.info("Agent description embeddings initialized")
        return result

    @property
    def agent_embeddings(self) -> Dict[str, List[float]]:
        if self._agent_embeddings is None:
            self._agent_embeddings = self._compute_agent_embeddings()
        return self._agent_embeddings

    def find_closest_agent(self, task: str, fallback: str = "Knowledge") -> str:
        embedder = self._get_embedder()
        try:
            task_vec = embedder.embed_query(task)
        except Exception:
            return fallback

        best_agent = fallback
        best_score = -1.0
        for agent_name, agent_vec in self.agent_embeddings.items():
            score = _cosine_similarity(task_vec, agent_vec)
            if score > best_score:
                best_score = score
                best_agent = agent_name

        logger.info(f"Semantic fallback routed to {best_agent} (score {best_score:.3f})")
        return best_agent

    def validate_plan(self, steps: List[List[Dict]]) -> List[List[Dict]]:
        validated = []
        for group in steps:
            validated_group = []
            for step in group:
                agent = step.get("agent", "Knowledge")
                if agent not in VALID_AGENTS:
                    corrected = self.find_closest_agent(step.get("task", ""))
                    logger.warning(f"Invalid agent '{agent}' corrected to '{corrected}'")
                    step = {**step, "agent": corrected}
                validated_group.append(step)
            validated.append(validated_group)
        return validated


class RouteAgent:
    """
    <module_purpose>
    <purpose>Acts as the central traffic controller, routing user intents to the correct sub-agent.</purpose>
    <metis_behavior>Relies exclusively on the HuggingFace Inference API to make deterministic routing decisions. All LLM-produced routes are validated by SemanticRouterValidator before entering the pipeline.</metis_behavior>
    </module_purpose>
    """

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
        self.validator = SemanticRouterValidator()

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

        except Exception:
            logger.exception("Semantic routing error")
            return {"route": "knowledge", "answer": ""}


semantic_router = RouteAgent()
plan_validator = SemanticRouterValidator()
