from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger
from core.config import settings

_hf_endpoint = HuggingFaceEndpoint(task="conversational", 
    repo_id=settings.LLAMA_MODEL,
    huggingfacehub_api_token=settings.HF_TOKEN,
    temperature=0.1
)
llm = ChatHuggingFace(llm=_hf_endpoint)

from src.schemas.plan import PlanStep, ExecutionPlan

class Planning:
    def __init__(self):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=ExecutionPlan)
        
    async def _invoke_llm(self, messages):
        import httpx
        try:
            return await self.llm.ainvoke(messages)
        except (httpx.TimeoutException, httpx.HTTPStatusError, Exception) as primary_err:
            logger.warning(f"Mô hình ngôn ngữ chính gặp sự cố ({primary_err})")
            raise primary_err
        
    async def create_plan(self, req) -> List[Dict[str, str]]:
        logger.info(f"Đang tạo kế hoạch cấu trúc cho truy vấn: {req.query}")
        
        from src.core.prompt_registry import prompt_registry, PromptType
        system_prompt = prompt_registry.get(PromptType.BRAIN_SYSTEM)
        
        history_str = ""
        if hasattr(req, "conversation_history") and req.conversation_history:
            history_str = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in req.conversation_history[-5:]])
            
        prompt = f"Recent conversation history:\n{history_str}\n\nLatest request: {req.query}\nCurrent context: {req.context if hasattr(req, 'context') else 'None'}"
        
        try:
            format_instructions = self.parser.get_format_instructions()
            messages = [
                SystemMessage(content=system_prompt.format(format_instructions=format_instructions)),
                HumanMessage(content=prompt)
            ]
            
            response = await self._invoke_llm(messages)
            
            parsed_result = self.parser.invoke(response)
            
            steps = [{"agent": step["agent"], "task": step["task"]} for step in parsed_result.get("steps", [])]
            
            if not steps:
                steps = [{"agent": "Knowledge", "task": "Trả lời người dùng rằng hệ thống không thể xử lý yêu cầu phức tạp này"}]
                
            return steps
            
        except Exception as e:
            logger.error(f"Tạo kế hoạch gặp sự cố do lỗi: {e}")
            return [{"agent": "KnowledgeAgent", "task": "Trả lời người dùng rằng hệ thống không thể xử lý yêu cầu phức tạp này do lỗi phân tích"}]

planning = Planning()
