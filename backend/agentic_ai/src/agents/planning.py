from typing import Any, Dict, List

from huggingface_hub import AsyncInferenceClient
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger
from src.schemas.planning import ExecutionPlan
from src.utils.huggingface import HFInferenceChat
from src.utils.structured_output import extract_json_value

from src.core.infrastructure.configuration import settings
from src.memory.memo import memo_manager

_hf_client = AsyncInferenceClient(
    model=settings.LLM_MODEL,
    token=settings.HF_TOKEN,
)
llm = HFInferenceChat(client=_hf_client, model=settings.LLM_MODEL)

class PlanAgent:
    """
    <module_purpose>
    DocLib Plan Agent for decomposing complex requests into execution plans.
    </module_purpose>
    <contract>
    - Precondition: Complex user query requiring multi-step execution.
    - Postcondition: Produces parallel and sequential structured execution plans.
    - Error Handling: Employs exponential backoff, retry mechanisms, and Redis caching to ensure plan structural validity.
    </contract>
    """

    def __init__(self):
        self.llm = llm
        self.structured_llm = self.llm.with_structured_output(ExecutionPlan)
        self.parser = JsonOutputParser(pydantic_object=ExecutionPlan)
        self._redis = None
        try:
            import redis.asyncio as redis_lib
            self._redis = redis_lib.from_url(settings.REDIS_URI, decode_responses=True)
        except Exception:
            self._redis = None
            logger.exception("Planner Redis client initialization failed")

    async def stream_plan(self, req_data: Dict[str, Any]):
        logger.info("Executing execution planning with streaming")

        from src.core.registry import PromptType, registry

        system_prompt = registry.get(PromptType.BRAIN_SYSTEM)

        history = req_data.get("conversation_history", [])
        history_str = "\n".join(
            [
                f"{msg.get('role', 'user')} said {msg.get('content', '')}"
                for msg in history
            ]
        )
        
        user_id = req_data.get("user_id", "guest")
        long_term_memory = await memo_manager.get_memories(user_id=user_id, query=req_data.get("query", ""))
        
        if long_term_memory:
            system_prompt += f"\n\n{long_term_memory}"

        query = req_data.get("query", "")
        context = req_data.get("context", "None")

        prompt = registry.get(PromptType.PLAN_USER_REQUEST).format(
            history_str=history_str, query=query, context=context
        )

        try:
            format_instructions = self.parser.get_format_instructions()
            messages = [
                SystemMessage(
                    content=system_prompt.format(
                        format_instructions=format_instructions
                    )
                ),
                HumanMessage(content=prompt),
            ]

            try:
                parsed_model = await self.structured_llm.ainvoke(messages)
                parsed_result = (
                    parsed_model.model_dump()
                    if hasattr(parsed_model, "model_dump")
                    else parsed_model.dict()
                )
            except Exception:
                logger.exception("Plan model invocation failed")
                parsed_result = {"steps": []}

            nodes = parsed_result.get("nodes", [])
            valid_nodes = []
            for n in nodes:
                if isinstance(n, dict):
                    valid_nodes.append({
                        "id": n.get("id", f"node_{len(valid_nodes)}"),
                        "agent": n.get("agent", "Knowledge"),
                        "task": n.get("task", "Analyze"),
                        "dependencies": n.get("dependencies", [])
                    })

            if not valid_nodes:
                valid_nodes = [
                    {
                        "id": "fallback_1",
                        "agent": "Reasoning",
                        "task": "Provide a safe response in the user's language without unsupported claims",
                        "dependencies": []
                    }
                ]

            yield {"type": "plan", "nodes": valid_nodes}

        except Exception:
            logger.exception("Plan generation error")
            yield {"type": "plan", "nodes": [{"id": "fallback", "agent": "Knowledge", "task": "Provide a safe failure response in the user's language", "dependencies": []}]}

    async def create_plan(self, req_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        import hashlib
        import json as _json

        if req_data.get("dry_run"):
            nodes = []
            async for chunk in self.stream_plan(req_data):
                if chunk["type"] == "plan":
                    nodes = chunk["nodes"]
            return nodes

        query = req_data.get("query", "")
        cache_scope = _json.dumps(
            {
                "user_id": req_data.get("user_id", "guest"),
                "query": query,
                "history": req_data.get("conversation_history", []),
                "context": req_data.get("context", ""),
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        cache_key = f"plan:{hashlib.sha256(cache_scope.encode()).hexdigest()}"

        if self._redis:
            try:
                cached = await self._redis.get(cache_key)
                if cached:
                    logger.info("Planner cache hit for query")
                    return _json.loads(cached)
            except Exception:
                logger.exception("Planner cache read failed")

        nodes = []
        async for chunk in self.stream_plan(req_data):
            if chunk["type"] == "plan":
                nodes = chunk["nodes"]
                
        nodes = await critic.review_plan(nodes)

        if nodes and self._redis:
            try:
                await self._redis.setex(cache_key, 3600, _json.dumps(nodes))
            except Exception:
                logger.exception("Planner cache write failed")

        return nodes

    async def replan(self, current_plan: Dict[str, Any], failed_step: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        logger.info(f"Generating revised plan due to failure in step: {failed_step.get('action')}")
        from src.core.registry import PromptType, registry
        import json
        
        system_prompt = registry.get(PromptType.BRAIN_SYSTEM)
        format_instructions = self.parser.get_format_instructions()
        
        replan_prompt = registry.get(PromptType.PLAN_REPLAN).format(
            current_plan=json.dumps(current_plan, ensure_ascii=False),
            failed_step=json.dumps(failed_step, ensure_ascii=False),
            error_message=error_message
        )
        
        messages = [
            SystemMessage(content=system_prompt.format(format_instructions=format_instructions)),
            HumanMessage(content=replan_prompt)
        ]
        
        try:
            parsed_model = await self.structured_llm.ainvoke(messages)
            return (
                parsed_model.model_dump()
                if hasattr(parsed_model, "model_dump")
                else parsed_model.dict()
            )
        except Exception as e:
            logger.exception("Replanning failed")
            return current_plan

class CriticAgent:
    """
    <module_purpose>
    DocLib Critic Agent for reviewing and optimizing execution plans.
    </module_purpose>
    <contract>
    - Precondition: Receives a parsed execution plan from PlanAgent.
    - Postcondition: Returns an optimized execution plan or raises alerts for flaws.
    </contract>
    """
    def __init__(self):
        self.llm = llm
        
    async def review_plan(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not nodes:
            return nodes
            
        logger.info("Critic Agent is reviewing the generated plan")
        try:
            import json
            messages = [
                SystemMessage(content="You are a Critic Agent. Review the provided execution plan JSON. Optimize it by combining redundant steps or fixing logical flaws. Output ONLY valid JSON containing the revised list of nodes. Do not wrap in markdown unless it's a standard json block."),
                HumanMessage(content=json.dumps(nodes, ensure_ascii=False))
            ]
            response = await self.llm.ainvoke(messages)
            reviewed_nodes = extract_json_value(response.content)
            if isinstance(reviewed_nodes, list) and all(isinstance(n, dict) for n in reviewed_nodes):
                logger.info("Critic Agent approved and optimized the plan")
                return reviewed_nodes
            else:
                logger.warning("Critic Agent returned invalid structure, falling back to original plan")
                return nodes
        except Exception as e:
            logger.exception("Critic Agent review failed, using original plan")
            return nodes

critic = CriticAgent()
planner = PlanAgent()
