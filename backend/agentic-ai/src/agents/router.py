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

    async def execute(self, query: str) -> dict:
        prompt = PromptTemplate(
            template="""Bạn là Router của hệ thống DocLib. Phân tích câu hỏi sau đây:
            Câu hỏi: {question}
            
            Nếu đây là một câu giao tiếp thông thường, hãy trả về định dạng JSON:
            {{"route": "chat"}}
            
            Nếu là yêu cầu nghiệp vụ, trả về JSON:
            {{"route": "knowledge"}} hoặc {{"route": "action"}}
            
            Chỉ trả về chuỗi JSON hợp lệ, không giải thích.""",
            input_variables=["question"]
        )
        try:
            from src.core.brain import llm
            import json
            
            res = await llm.ainvoke(prompt.format(question=query))
            content = res.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            try:
                decision = json.loads(content)
            except Exception:
                decision = {"route": "knowledge"}
                if "action" in content.lower():
                    decision["route"] = "action"
                elif "chat" in content.lower():
                    decision["route"] = "chat"
                    
            route = decision.get("route", "knowledge").lower()
            answer = decision.get("answer", "")
            
            if route not in ["chat", "action", "knowledge"]:
                route = "knowledge"
                
            logger.info(f"RouterAgent: Classified request as route='{route}'")
            return {"route": route, "answer": answer}
            
        except Exception as e:
            logger.error(f"RouterAgent: Routing failed: {e}")
            return {"route": "knowledge", "answer": ""}

router_agent = RouterAgent()
