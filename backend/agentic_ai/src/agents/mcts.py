import hashlib
import json
import math
from typing import Any, Dict, List, Optional

import redis
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.registry import PromptType, registry
from src.schemas.mcts import MCTSEvaluation, MCTSThoughts


def _get_redis_client() -> Optional[redis.Redis]:
    try:
        r = redis.from_url(settings.REDIS_URI, decode_responses=True)
        r.ping()
        return r
    except Exception:
        logger.exception("MCTS Redis connection failed")
        return None


class MCTSNode:
    def __init__(self, state: Dict[str, Any], parent: Optional["MCTSNode"] = None):
        self.state = state
        self.parent = parent
        self.children: List["MCTSNode"] = []
        self.visits = 0
        self.value = 0.0

    def add_child(self, child_state: Dict[str, Any]) -> "MCTSNode":
        child = MCTSNode(state=child_state, parent=self)
        self.children.append(child)
        return child

    def uct_score(self, exploration_weight: float = 1.414) -> float:
        if self.visits == 0:
            return float("inf")
        exploitation = self.value / self.visits
        exploration = exploration_weight * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

class MCTSGenerator:
    """
    <agent_role>
    <identity>MCTS Thought Branch Generator</identity>
    <responsibility>Generates diverse, parallel solution branches for complex logical tasks.</responsibility>
    <metis_behavior>Employs strict heuristic evaluation, alpha-beta pruning, and Redis caching to traverse the optimal execution path efficiently.</metis_behavior>
    </agent_role>
    """

    def __init__(self, llm, evaluator_llm, max_iterations: int = 5):
        self.llm = llm
        self.evaluator_llm = evaluator_llm
        self.max_iterations = max_iterations
        self._redis = _get_redis_client()

    def _cache_key(self, task: str) -> str:
        return f"mcts:{hashlib.sha256(task.encode()).hexdigest()}"

    def _load_cache(self, task: str) -> Optional[Dict[str, Any]]:
        if not self._redis:
            return None
        try:
            raw = self._redis.get(self._cache_key(task))
            if raw:
                logger.info("MCTS cache hit for task")
                return json.loads(raw)
        except Exception:
            logger.exception("MCTS cache read failed")
        return None

    def _save_cache(self, task: str, state: Dict[str, Any]):
        if not self._redis:
            return
        try:
            self._redis.setex(self._cache_key(task), 86400, json.dumps(state))
            logger.info("MCTS result cached to Redis")
        except Exception:
            logger.exception("MCTS cache write failed")

    async def _estimate_complexity(self, task: str) -> int:
        words = len(task.split())
        if words < 20:
            return 5
        if words < 60:
            return 10
        return 15

    async def generate_thoughts(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Executing LLM branch generation logic")
        system_prompt = registry.get(PromptType.SWARM_MCTS_GENERATOR)
        human_msg = f"Task: {state.get('task', '')}\nBase Code:\n{state.get('code', '')}"
        try:
            structured_llm = self.llm.with_structured_output(MCTSThoughts)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            response = await structured_llm.ainvoke(messages)
            new_states = []
            for branch in response.branches:
                new_state = state.copy()
                new_state["approach"] = branch.approach_name
                new_state["code"] = branch.implementation
                new_states.append(new_state)
            return new_states
        except Exception:
            logger.exception("LLM branch generation failed")
            return []

    async def evaluate_state(self, state: Dict[str, Any]) -> float:
        logger.info("Executing LLM heuristic evaluation logic")
        system_prompt = registry.get(PromptType.SWARM_MCTS_EVALUATOR)
        human_msg = f"Code:\n{state.get('code', '')}"
        try:
            structured_evaluator = self.evaluator_llm.with_structured_output(MCTSEvaluation)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            eval_result = await structured_evaluator.ainvoke(messages)
            return eval_result.score
        except Exception:
            logger.exception("LLM evaluation failed")
            return 0.5

    def _prune_weak_branches(self, node: MCTSNode):
        if len(node.children) < 2:
            return
        scores = [c.uct_score() for c in node.children]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = math.sqrt(variance) if variance > 0 else 0.0
        threshold = mean - std
        node.children = [c for c in node.children if c.uct_score() >= threshold]

    async def search(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        task = initial_state.get("task", "")
        cached = self._load_cache(task)
        if cached:
            return cached

        iterations = await self._estimate_complexity(task)
        root = MCTSNode(state=initial_state)

        for i in range(iterations):
            node = root
            while node.children:
                node = max(node.children, key=lambda c: c.uct_score())

            if node.visits > 0 or node == root:
                new_states = await self.generate_thoughts(node.state)
                for ns in new_states:
                    node.add_child(ns)
                if node.children:
                    node = node.children[0]

            score = await self.evaluate_state(node.state)

            curr = node
            while curr is not None:
                curr.visits += 1
                curr.value += score
                curr = curr.parent

            if i % 3 == 2:
                self._prune_weak_branches(root)

        if not root.children:
            return root.state

        best_node = max(root.children, key=lambda c: c.visits)
        logger.info("MCTS branch selection completed successfully")

        result = best_node.state
        self._save_cache(task, result)
        return result
