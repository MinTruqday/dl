import time
import re
from loguru import logger
from typing import List
from src.core.prompt_registry import prompt_registry, PromptType

_INJECTION_PATTERN = re.compile(
    r"(system[_\s]?prompt|api[_\s]?key|secret[_\s]?key|hf[_\s]?token"
    r"|ignore (previous|above|all)|jailbreak|do anything now|dan mode"
    r"|bypass (safety|filter|restriction))",
    re.IGNORECASE
)

def _contains_injection(text: str) -> bool:
    return bool(_INJECTION_PATTERN.search(text))


class ResponseGenerator:
    def __init__(self):
        pass
        
    async def aggregate_stream(self, query: str, consolidated_results: List[str]):
        logger.info(f"Đang tổng hợp kết quả cho truy vấn: {query[:50]}")
        
        if _contains_injection(query):
            logger.warning("Phát hiện dấu hiệu chèn mã độc vào câu truy vấn")
            yield "Yêu cầu này vi phạm chính sách sử dụng. Vui lòng đặt câu hỏi khác"
            return
        
        try:
            from src.agents.planning import llm
            from langchain_core.messages import HumanMessage
            
            gathered_data = "\n\n".join(consolidated_results)
            if len(gathered_data) > 12000:
                gathered_data = gathered_data[:12000]
                
            final_prompt = prompt_registry.get(PromptType.AGGREGATOR).format(query=query, gathered_data=gathered_data)
            
            async for chunk in llm.astream([HumanMessage(content=final_prompt)]):
                if chunk.content:
                    yield chunk.content
            
        except Exception as e:
            logger.error(f"Lỗi tạo phản hồi: {str(e)}")
            yield "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

response_generator = ResponseGenerator()