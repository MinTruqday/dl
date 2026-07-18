import json
from typing import Any, Dict, List, Optional

import httpx
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from loguru import logger
from pydantic import BaseModel, Field
from src.schemas.planning import ExecutionPlan, PlanNode
from src.utils.resilience import with_retry

from src.core.infrastructure.configuration import settings

_hf_endpoint = HuggingFaceEndpoint(
    task="conversational",
    repo_id=settings.LLM_MODEL,
    huggingfacehub_api_token=settings.HF_TOKEN,
    temperature=0.1,
)
llm = ChatHuggingFace(llm=_hf_endpoint)

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
        self.parser = JsonOutputParser(pydantic_object=ExecutionPlan)
        self._redis = None
        try:
            import redis as redis_lib
            self._redis = redis_lib.from_url(settings.REDIS_URI, decode_responses=True)
            self._redis.ping()
        except Exception:
            logger.exception("Planner Redis connection failed")

    @with_retry(max_retries=3, base_wait=2, max_wait=10)
    async def _invoke_llm(self, messages):
        return await self.llm.ainvoke(messages)

    async def stream_plan(self, req_data: Dict[str, Any]):
        logger.info("Executing execution planning with streaming")

        from src.core.registry import PromptType, registry

        system_prompt = registry.get(PromptType.BRAIN_SYSTEM)

        history = req_data.get("conversation_history", [])
        history_str = "\n".join(
            [
                f"{msg.get('role', 'user')} said {msg.get('content', '')}"
                for msg in history[-5:]
            ]
        )

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

            accumulated_json = ""
            think_ended = False

            async for chunk in self.llm.astream(messages):
                if not chunk.content:
                    continue
                content = chunk.content

                if think_ended:
                    accumulated_json += content
                else:
                    if "</think>" in content or "```json" in content:
                        think_ended = True
                        split_str = "</think>" if "</think>" in content else "```json"
                        parts = content.split(split_str)
                        if parts[0]:
                            yield {"type": "message", "chunk": parts[0] + ("</think>\n" if split_str == "</think>" else "")}
                        if len(parts) > 1:
                            accumulated_json += ("```json" if split_str == "```json" else "") + parts[1]
                    else:
                        yield {"type": "message", "chunk": content}

            if not accumulated_json.strip():
                parsed_result = {"steps": []}
            else:
                try:
                    parsed_result = self.parser.invoke(AIMessage(content=accumulated_json))
                except Exception:
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
                        "agent": "Knowledge",
                        "task": "Inform user request exceeds capabilities",
                        "dependencies": []
                    }
                ]

            yield {"type": "plan", "nodes": valid_nodes}

        except Exception as e:
            logger.exception("Plan generation error")
            yield {"type": "plan", "nodes": [{"id": "fallback", "agent": "Knowledge", "task": f"Inform user about analysis failure {e}", "dependencies": []}]}

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
        cache_key = f"plan:{hashlib.sha256(query.encode()).hexdigest()}"

        if self._redis:
            try:
                cached = self._redis.get(cache_key)
                if cached:
                    logger.info("Planner cache hit for query")
                    return _json.loads(cached)
            except Exception:
                logger.exception("Planner cache read failed")

        nodes = []
        async for chunk in self.stream_plan(req_data):
            if chunk["type"] == "plan":
                nodes = chunk["nodes"]

        if nodes and self._redis:
            try:
                self._redis.setex(cache_key, 3600, _json.dumps(nodes))
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
            response = await self._invoke_llm(messages)
            content_str = response.content
            if "</think>" in content_str:
                content_str = content_str.split("</think>")[-1].strip()
            if "```json" in content_str:
                content_str = content_str.split("```json")[1].split("```")[0].strip()
            
            parsed_plan = self.parser.parse(content_str)
            return parsed_plan
        except Exception as e:
            logger.exception("Replanning failed")
            return current_plan

planner = PlanAgent()
