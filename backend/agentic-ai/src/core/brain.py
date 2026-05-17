from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from loguru import logger
from src.core.config import settings

_hf_endpoint = HuggingFaceEndpoint(
    repo_id=settings.LLAMA_MODEL,
    huggingfacehub_api_token=settings.HF_TOKEN,
    temperature=0.1
)
llm = ChatHuggingFace(llm=_hf_endpoint)

class AgenticBrain:
    def __init__(self):
        self.llm = llm
        
    async def create_plan(self, req) -> List[Dict[str, str]]:
        logger.info(f"Brain: Creating plan for query: {req.query}")
        
        system_prompt = """Bạn là Core Brain của hệ thống Agentic AI. Nhiệm vụ của bạn là phân rã yêu cầu của người dùng thành một kế hoạch chi tiết với các bước nhỏ hơn.
Các công cụ/Agent mà hệ thống có sẵn (Bạn KHÔNG tự thực thi, chỉ định tuyến):
1. RAGAgent: Đọc, tìm kiếm và phân tích tài liệu nội bộ (sách, PDF, file đính kèm) từ thư viện người dùng.
2. CodeInterpreter: Viết và chạy mã Python (ví dụ: vẽ biểu đồ, tính toán phức tạp).
3. SearchEngine: Tìm kiếm thông tin trên internet toàn cầu.
4. ActionAgent: Truy xuất và thao tác dữ liệu hệ thống nội bộ (Ví tiền, Doanh thu, Tài liệu cá nhân, ...).
5. DraftGenerator: Tạo nháp văn bản, sinh mã LaTeX, lưu trữ file.

Dựa trên yêu cầu của người dùng, hãy viết danh sách các bước. Trả về DUY NHAT định dạng JSON array, không có text nào khác. Ví dụ:
[
  {"agent": "ActionAgent", "task": "Kiểm tra số dư ví tiền của người dùng"},
  {"agent": "CodeInterpreter", "task": "Tính toán biểu đồ tăng trưởng"}
]"""

        history_str = ""
        if hasattr(req, "conversation_history") and req.conversation_history:
            history_str = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in req.conversation_history[-5:]])
            
        prompt = f"Lịch sử trò chuyện gần đây:\n{history_str}\n\nYêu cầu mới nhất: {req.query}\nNgữ cảnh hiện tại: {req.context if hasattr(req, 'context') else 'Không có'}\n\nKế hoạch thực thi (JSON):"
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            steps = json.loads(content)
            if not isinstance(steps, list):
                steps = [{"agent": "ActionAgent", "task": "Xử lý trực tiếp yêu cầu"}]
            return steps
        except Exception as e:
            logger.error(f"Brain: Plan creation failed: {e}")
            return [{"agent": "Aggregator", "task": "Phản hồi lỗi hệ thống cho người dùng"}]

brain = AgenticBrain()
