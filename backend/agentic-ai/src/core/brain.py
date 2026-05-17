from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
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
        self.parser = JsonOutputParser(pydantic_object=ExecutionPlan)
        
    async def create_plan(self, req) -> List[Dict[str, str]]:
        logger.info(f"Brain: Creating structured plan for query: {req.query}")
        
        system_prompt = """Bạn là Core Brain của hệ thống Agentic AI. Nhiệm vụ của bạn là phân rã yêu cầu của người dùng thành một kế hoạch chi tiết với các bước nhỏ hơn.
Các công cụ/Agent mà hệ thống có sẵn (Bạn KHÔNG tự thực thi, chỉ định tuyến):
1. KnowledgeAgent: Đọc, tìm kiếm và phân tích tài liệu nội bộ (sách, PDF, file đính kèm) từ thư viện người dùng.
2. CodeInterpreter: Viết và chạy mã Python (ví dụ: vẽ biểu đồ, tính toán phức tạp, xử lý chuỗi/mảng).
3. SearchEngine: Tìm kiếm thông tin cập nhật trên internet toàn cầu.
4. ActionAgent: Truy xuất và thao tác dữ liệu hệ thống nội bộ (Ví tiền, Doanh thu, Tài liệu cá nhân, ...).
5. DraftGenerator: Tạo nháp văn bản, sinh mã LaTeX, xử lý format.

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
            
            response = await self.llm.ainvoke(messages)
            
            parsed_result = self.parser.invoke(response)
            
            steps = [{"agent": step["agent"], "task": step["task"]} for step in parsed_result.get("steps", [])]
            
            if not steps:
                steps = [{"agent": "ActionAgent", "task": "Xử lý trực tiếp yêu cầu"}]
                
            return steps
            
        except Exception as e:
            logger.error(f"Brain: Plan creation failed: {e}")
            return [{"agent": "ActionAgent", "task": req.query}]

brain = AgenticBrain()

