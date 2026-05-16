from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from loguru import logger
from src.core.config import settings

class Plan(BaseModel):
    steps: List[str] = Field(description="Các bước thực thi logic tuần tự")
    
_hf_endpoint = HuggingFaceEndpoint(
    repo_id=settings.LLAMA_MODEL,
    huggingfacehub_api_token=settings.HF_TOKEN,
    temperature=0.1
)
llm = ChatHuggingFace(llm=_hf_endpoint)

class AgenticBrain:
    def __init__(self):
        self.llm = llm
        
    async def create_plan(self, req) -> List[str]:
        """Tạo kế hoạch phân rã tác vụ (Multi-step Decomposition)."""
        logger.info(f"Brain: Tạo kế hoạch cho query: {req.query}")
        
        system_prompt = """Bạn là Core Brain của hệ thống Agentic AI. Nhiệm vụ của bạn là phân rã yêu cầu của người dùng thành một kế hoạch chi tiết với các bước nhỏ bé hơn.
Các công cụ/Agent mà hệ thống có sẵn (Bạn KHÔNG tự thực thi, chỉ định tuyến):
1. RAGAgent: Đọc, tìm kiếm và phân tích tài liệu nội bộ (sách, PDF, file đính kèm) từ thư viện người dùng. Dùng công cụ này BẤT CỨ KHI NÀO người dùng hỏi về tài liệu, sách, hoặc kho tri thức nội bộ.
2. CodeInterpreter: Viết và chạy mã Python (ví dụ: vẽ biểu đồ, tính toán phức tạp).
3. SearchEngine: Tìm kiếm thông tin trên internet toàn cầu. Dùng khi thông tin không có trong tài liệu nội bộ.
4. InternalAPI: Truy xuất dữ liệu hệ thống nội bộ (Ví tiền, Doanh thu, ...).
5. DraftGenerator: Tạo nháp văn bản, sinh mã LaTeX, lưu trữ file.

Dựa trên yêu cầu của người dùng, hãy viết danh sách các bước. Trả về định dạng:
Bước 1: [Tên Agent] - [Mô tả chi tiết tác vụ]
Bước 2: [Tên Agent] - [Mô tả chi tiết tác vụ]
...

Hãy chỉ trả về các bước, không giải thích thêm."""

        history_str = ""
        if hasattr(req, "conversation_history") and req.conversation_history:
            history_str = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in req.conversation_history[-5:]])
            
        prompt = f"Lịch sử trò chuyện gần đây:\n{history_str}\n\nYêu cầu mới nhất: {req.query}\nNgữ cảnh hiện tại: {req.context if hasattr(req, 'context') else 'Không có'}\n\nKế hoạch thực thi:"
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            steps = []
            for line in content.split('\n'):
                if line.lower().startswith("bước") or line.lower().startswith("step") or line.strip().startswith("-") or line.strip().startswith(tuple(str(i) for i in range(1, 10))):
                    steps.append(line.strip())
            
            if not steps:
                steps = ["Bước 1: InternalAPI - Xử lý trực tiếp yêu cầu"]
                
            return steps
        except Exception as e:
            logger.error(f"Brain: Lỗi tạo kế hoạch: {e}")
            return ["Bước 1: Aggregator - Phản hồi lỗi hệ thống cho người dùng"]

brain = AgenticBrain()
