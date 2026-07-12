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
    def __init__(self):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=ExecutionPlan)

    @with_retry(max_retries=3, base_wait=2, max_wait=10)
    async def _invoke_llm(self, messages):
        return await self.llm.ainvoke(messages)

    async def create_plan(self, req_data: Dict[str, Any]) -> List[Dict[str, str]]:
        logger.info("Executing execution planning")

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

            response = await self._invoke_llm(messages)
            parsed_result = self.parser.invoke(response)

            steps = []
            for step_group in parsed_result.get("steps", []):
                group = [{"agent": s["agent"], "task": s["task"]} for s in step_group.get("parallel_steps", [])]
                if group:
                    steps.append(group)

            if not steps:
                steps = [
                    [
                        {
                            "agent": "Knowledge",
                            "task": "Inform user request exceeds capabilities",
                        }
                    ]
                ]

            return steps

        except Exception as e:
            logger.exception("Plan generation error")
            return [[{"agent": "Knowledge", "task": f"Inform user about analysis failure {e}"}]]

planner = PlanAgent()
