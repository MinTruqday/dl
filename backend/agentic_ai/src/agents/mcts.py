import math
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from src.schemas.mcts import MCTSThoughts, MCTSEvaluation, ThoughtBranch
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
from src.core.registry import PromptType, registry

class MCTSNode:
    def __init__(self, state: Dict[str, Any], parent=None):
        self.state = state
        self.parent = parent
        self.children: List['MCTSNode'] = []
        self.visits = 0
        self.value = 0.0
        
    def add_child(self, child_state: Dict[str, Any]) -> 'MCTSNode':
        child = MCTSNode(state=child_state, parent=self)
        self.children.append(child)
        return child
        
    def uct_score(self, exploration_weight=1.414) -> float:
        if self.visits == 0:
            return float('inf')
        
        exploitation = self.value / self.visits
        exploration = exploration_weight * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

class MCTSGenerator:
    """
    <agent_role>
    <identity>MCTS Thought Branch Generator</identity>
    <responsibility>Generates diverse, parallel solution branches for complex logical tasks.</responsibility>
    <metis_behavior>Employs strict heuristic evaluation to traverse the most optimal execution path.</metis_behavior>
    </agent_role>
    """
    def __init__(self, llm, evaluator_llm, max_iterations=3):
        self.llm = llm
        self.evaluator_llm = evaluator_llm
        self.max_iterations = max_iterations
        
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
        except Exception as e:
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
        except Exception as e:
            logger.exception("LLM evaluation failed")
            return 0.5
        
    async def search(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        root = MCTSNode(state=initial_state)
        
        for _ in range(self.max_iterations):
            node = root
            while node.children:
                node = max(node.children, key=lambda c: c.uct_score())
                
            if node.visits > 0 or node == root:
                new_states = await self.generate_thoughts(node.state)
                for ns in new_states:
                    node.add_child(ns)
                node = node.children[0] if node.children else node
                
            score = await self.evaluate_state(node.state)
            
            curr = node
            while curr is not None:
                curr.visits += 1
                curr.value += score
                curr = curr.parent
                
        if not root.children:
            return root.state
            
        best_node = max(root.children, key=lambda c: c.visits)
        logger.info("MCTS branch selection completed successfully")
        return best_node.state
