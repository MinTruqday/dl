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
        
    async def create_plan(self, query: str, context: Optional[str] = None) -> List[str]:
        logger.info(f"Brain: Tạo kế hoạch cho query: {query}")
        
        system_prompt = """Bạn là Core Brain của hệ thống Agentic AI. Nhiệm vụ của bạn là phân rã yêu cầu của người dùng thành một kế hoạch chi tiết với các bước nhỏ bé hơn.
Các công cụ/Agent mà hệ thống có sẵn (Bạn KHÔNG tự thực thi, chỉ định tuyến):
1. CodeInterpreter: Viết và chạy mã Python (ví dụ: vẽ biểu đồ, tính toán phức tạp).
2. SearchEngine: Tìm kiếm thông tin trên internet.
3. InternalAPI: Truy xuất dữ liệu hệ thống nội bộ (Tài liệu, Ví tiền, Doanh thu, ...).
4. DraftGenerator: Tạo nháp văn bản, sinh mã LaTeX, lưu trữ file.

Dựa trên yêu cầu của người dùng, hãy viết danh sách các bước. Trả về định dạng:
Bước 1: [Tên Agent] - [Mô tả chi tiết tác vụ]
Bước 2: [Tên Agent] - [Mô tả chi tiết tác vụ]
...

Hãy chỉ trả về các bước, không giải thích thêm."""

        prompt = f"Yêu cầu: {query}\nNgữ cảnh hiện tại: {context or 'Không có'}\n\nKế hoạch thực thi:"
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
