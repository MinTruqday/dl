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
    "MCTSAgent": "Solves complex logic problems by exploring multiple solution branches via Monte Carlo Tree Search"
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

    async def _compute_agent_embeddings(self) -> Dict[str, List[float]]:
        embedder = self._get_embedder()
        result = {}
        for agent_name, description in VALID_AGENTS.items():
            try:
                vec = await embedder.embed_query(description)
                result[agent_name] = vec
            except Exception:
                logger.exception(f"Failed to embed agent description for {agent_name}")
        logger.info("Agent description embeddings initialized")
        return result

    async def get_agent_embeddings(self) -> Dict[str, List[float]]:
        if self._agent_embeddings is None:
            self._agent_embeddings = await self._compute_agent_embeddings()
        return self._agent_embeddings

    async def find_closest_agent(self, task: str, fallback: str = "Knowledge") -> str:
        embedder = self._get_embedder()
        try:
            task_vec = await embedder.embed_query(task)
        except Exception:
            return fallback

        best_agent = fallback
        best_score = -1.0
        for agent_name, agent_vec in (await self.get_agent_embeddings()).items():
            score = _cosine_similarity(task_vec, agent_vec)
            if score > best_score:
                best_score = score
                best_agent = agent_name

        logger.info(f"Semantic fallback routed to {best_agent} (score {best_score:.3f})")
        return best_agent

    async def validate_plan(self, nodes: List[Dict]) -> List[Dict]:
        validated = []
        for node in nodes:
            agent = node.get("agent", "Knowledge")
            task_desc = node.get("task", "")
            if agent not in VALID_AGENTS:
                corrected = await self.find_closest_agent(task_desc)
                logger.warning(f"Invalid agent '{agent}' corrected to '{corrected}'")
                node = {**node, "agent": corrected}
                agent = corrected
            validated.append(node)
        return validated


INTENTS = {
    "chat": "Conversational chat, greetings, casual talk and social exchanges",
    "action": "Authenticated system mutations and registered tool operations",
    "knowledge": "Document retrieval, factual questions, analysis and content generation"
}

class RouteAgent:
    """
    <module_purpose>
    <purpose>Acts as the central traffic controller, routing user intents to the correct sub-agent.</purpose>
    <metis_behavior>Uses Vector Embeddings for fast, deterministic intent classification with a confidence threshold, falling back to LLM or Knowledge route if uncertain.</metis_behavior>
    </module_purpose>
    """
    def __init__(self):
        self._intent_vecs = None

    def _get_embedder(self):
        from src.rag.embedding import embedder
        return embedder

    async def _get_intent_vecs(self):
        if self._intent_vecs is None:
            embedder = self._get_embedder()
            self._intent_vecs = {}
            for intent, desc in INTENTS.items():
                self._intent_vecs[intent] = await embedder.embed_query(desc)
        return self._intent_vecs

    async def execute(self, query: str) -> dict:
        embedder = self._get_embedder()
        try:
            query_vec = await embedder.embed_query(query)
            best_route = "knowledge"
            best_score = -1.0
            
            for intent, vec in (await self._get_intent_vecs()).items():
                score = _cosine_similarity(query_vec, vec)
                if score > best_score:
                    best_score = score
                    best_route = intent

            if best_score > settings.AGENT_ROUTE_CONFIDENCE_THRESHOLD:
                logger.info(f"Intent classified as {best_route} with confidence {best_score:.3f}")
                return {"route": best_route, "answer": ""}
            else:
                logger.warning(f"Low confidence intent ({best_score:.3f}). Defaulting to knowledge")
                return {"route": "knowledge", "answer": ""}
                
        except Exception:
            logger.exception("Semantic routing error")
            return {"route": "knowledge", "answer": ""}

semantic_router = RouteAgent()
plan_validator = SemanticRouterValidator()
