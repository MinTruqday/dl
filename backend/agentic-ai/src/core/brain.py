from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger
from src.core.config import settings

_hf_endpoint = HuggingFaceEndpoint(
    repo_id=settings.LLAMA_MODEL,
    huggingfacehub_api_token=settings.HF_TOKEN,
    temperature=0.1
)
llm = ChatHuggingFace(llm=_hf_endpoint)

from src.models.plan import PlanStep, ExecutionPlan

class AgenticBrain:
    def __init__(self):
        self.llm = llm
        try:
            self.fallback_llm = ChatOllama(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL, temperature=0.1)
        except Exception as e:
            logger.warning(f"Brain: Could not initialize Ollama fallback: {e}")
            self.fallback_llm = None
        self.parser = JsonOutputParser(pydantic_object=ExecutionPlan)
        
    async def _invoke_llm(self, messages):
        import httpx
        try:
            return await self.llm.ainvoke(messages)
        except (httpx.TimeoutException, httpx.HTTPStatusError, Exception) as primary_err:
            logger.warning(f"Brain: Primary LLM failed ({primary_err}).")
            if self.fallback_llm:
                logger.info("Brain: Falling back to Ollama LLM.")
                try:
                    return await self.fallback_llm.ainvoke(messages)
                except Exception as fallback_err:
                    logger.error(f"Brain: Fallback LLM also failed: {fallback_err}")
                    raise Exception("Tất cả dịch vụ LLM đều không phản hồi.")
            else:
                raise primary_err
        
    async def create_plan(self, req) -> List[Dict[str, str]]:
        logger.info(f"Brain: Creating structured plan for query: {req.query}")
        
        system_prompt = """Bạn là Core Brain của hệ thống Agentic AI. Nhiệm vụ của bạn là phân rã yêu cầu của người dùng thành một kế hoạch chi tiết với các bước nhỏ hơn.
Các công cụ/Agent mà hệ thống có sẵn (Bạn KHÔNG tự thực thi, chỉ định tuyến):
1. KnowledgeAgent: Đọc, tìm kiếm và phân tích tài liệu nội bộ từ thư viện.
2. CodeInterpreter: Viết và thực thi mã Python để xử lý các tác vụ lập trình.
3. SearchEngine: Tìm kiếm thông tin mở rộng trên internet toàn cầu.
4. ActionAgent: Truy xuất và thao tác dữ liệu với hệ thống nội bộ.
5. DraftGenerator: Tạo nháp văn bản và định dạng cấu trúc nội dung.
6. ReasoningAgent: Đánh giá chất lượng, phân tích logic sâu và suy luận đa chiều.

Lưu ý: BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON HỢP LỆ THEO YÊU CẦU DƯỚI ĐÂY.
{format_instructions}"""
        
        history_str = ""
        if hasattr(req, "conversation_history") and req.conversation_history:
            history_str = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in req.conversation_history[-5:]])
            
        prompt = f"Lịch sử trò chuyện gần đây:\n{history_str}\n\nYêu cầu mới nhất: {req.query}\nNgữ cảnh hiện tại: {req.context if hasattr(req, 'context') else 'Không có'}\n\nHãy lập kế hoạch:"
        
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
                steps = [{"agent": "ActionAgent", "task": "Xử lý trực tiếp yêu cầu"}]
                
            return steps
            
        except Exception as e:
            logger.error(f"Brain: Plan creation failed: {e}")
            return [{"agent": "ActionAgent", "task": req.query}]

brain = AgenticBrain()

