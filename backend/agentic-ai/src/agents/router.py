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
            - "knowledge": Các yêu cầu về tra cứu kiến thức, xử lý thông tin, phân tích và suy luận nội dung.
            - "action": Các yêu cầu thao tác thực thi nghiệp vụ, thay đổi dữ liệu hoặc điều khiển hệ thống.
            - "chat": Các câu giao tiếp thông thường mang tính chất trò chuyện, hỏi đáp cơ bản không liên quan đến nghiệp vụ sâu.

            Trả lời duy nhất "knowledge", "action" hoặc "chat":""",
            input_variables=["question"]
        )
        try:
            from src.core.brain import llm
            res = await llm.ainvoke(prompt.format(question=query))
            decision = res.content.strip().lower()
            if "action" in decision:
                route = "action"
            elif "chat" in decision:
                route = "chat"
            else:
                route = "knowledge"
        except Exception as e:
            logger.error(f"RouterAgent: Routing failed: {e}")
            route = "knowledge"
            
        logger.info(f"RouterAgent: Classified request as route='{route}'")
        return route

router_agent = RouterAgent()
