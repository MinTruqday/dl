from loguru import logger
from langchain_core.prompts import PromptTemplate
from src.core.config import settings
from huggingface_hub import AsyncInferenceClient
from src.utils.hf import HFInferenceChat

class RouterAgent:
    def __init__(self):
        llama_model = settings.LLAMA_MODEL
        if not llama_model:
            raise ValueError("LLAMA_MODEL is not set")
            
        self.llama_client = AsyncInferenceClient(
            model=settings.LLAMA_MODEL,
            token=settings.HF_TOKEN,
        )
        self.router_llm = HFInferenceChat(client=self.llama_client, model=settings.LLAMA_MODEL)

    async def execute(self, query: str) -> str:
        prompt = PromptTemplate(
            template="""Bạn là Cổng kiểm duyệt (Router) của hệ thống DocLib. Phân tích ý định câu hỏi và chuyển hướng.
            
            Quy tắc định tuyến:
            - "rag": Câu hỏi liên quan đến nội dung tài liệu, giải thích đoạn văn, tóm tắt.
            - "action": Các yêu cầu thao tác trên hệ thống như: xem số dư, nạp tiền, thanh toán, quản lý thư viện cá nhân, xóa/khôi phục file, xem thống kê.
            - "chat": Câu hỏi giao tiếp thông thường, chào hỏi (Ví dụ: Xin chào, bạn khỏe không, cảm ơn).
            
            Câu hỏi: {question}
            Trả lời duy nhất "rag", "action" hoặc "chat":""",
            input_variables=["question"]
        )
        try:
            response = await self.router_llm.ainvoke(prompt.format(question=query))
            decision = response.content.strip().lower()
        except Exception as e:
            logger.error(f"Router LLM error: {e}")
            decision = "rag"
        
        route = "rag" 
        if "action" in decision: route = "action"
        elif "chat" in decision: route = "chat"
        
        logger.info(f"RouterAgent: Classified request as route='{route}'")
        return route

router_agent = RouterAgent()
