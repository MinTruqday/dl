import asyncio
from typing import Any, Callable, Dict, List
from loguru import logger
from src.workflow.state import ActingState

class WorkflowExecutor:
    @staticmethod
    async def execute_task_node(node: Dict[str, Any], state: ActingState, agent_fn: Callable) -> Dict[str, Any]:
        node_id = node.get("id", "")
        task_name = node.get("name", "task")
        try:
            res = await agent_fn(state)
            return {"node_id": node_id, "status": "completed", "result": res}
        except Exception as e:
            logger.exception(f"Error executing task {node_id} ({task_name})")
            return {"node_id": node_id, "status": "failed", "error": str(e)}

    @staticmethod
    async def execute_parallel_nodes(nodes: List[Dict[str, Any]], state: ActingState, agent_map: Dict[str, Callable]) -> List[Dict[str, Any]]:
        tasks = []
        for node in nodes:
            agent_type = node.get("agent_type", "actor")
            agent_fn = agent_map.get(agent_type)
            if agent_fn:
                tasks.append(WorkflowExecutor.execute_task_node(node, state, agent_fn))
        return await asyncio.gather(*tasks, return_exceptions=False)
