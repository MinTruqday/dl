import json
from typing import Any, Dict, List, Optional

import httpx
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from loguru import logger
from pydantic import BaseModel, Field
from src.schemas.planning import ExecutionPlan, PlanStep
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
    <purpose>Decomposes complex requests into parallel and sequential execution plans.</purpose>
    <metis_behavior>Employs exponential backoff and retry mechanisms to guarantee structural validity of the plan.</metis_behavior>
    </module_purpose>
    """
    def __init__(self):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=ExecutionPlan)

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
                # fallback if no clear separation found
                parsed_result = {"steps": []}
            else:
                try:
                    parsed_result = self.parser.invoke(AIMessage(content=accumulated_json))
                except Exception:
                    parsed_result = {"steps": []}

            steps = []
            for step_group in parsed_result.get("steps", []):
                if isinstance(step_group, dict):
                    group = [{"agent": s.get("agent", "Knowledge"), "task": s.get("task", "Analyze")} for s in step_group.get("parallel_steps", []) if isinstance(s, dict)]
                    if group:
                        steps.append(group)
                elif isinstance(step_group, str):
                    steps.append([{"agent": "Knowledge", "task": step_group}])

            if not steps:
                steps = [
                    [
                        {
                            "agent": "Knowledge",
                            "task": "Inform user request exceeds capabilities",
                        }
                    ]
                ]

            yield {"type": "plan", "steps": steps}

        except Exception as e:
            logger.exception("Plan generation error")
            yield {"type": "plan", "steps": [[{"agent": "Knowledge", "task": f"Inform user about analysis failure {e}"}]]}

    async def create_plan(self, req_data: Dict[str, Any]) -> List[Dict[str, str]]:
        steps = []
        async for chunk in self.stream_plan(req_data):
            if chunk["type"] == "plan":
                steps = chunk["steps"]
        return steps

planner = PlanAgent()
