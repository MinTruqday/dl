import time
from loguru import logger
from typing import List

class AggregatorAgent:
    def __init__(self):
        pass
        
    async def aggregate(self, query: str, consolidated_results: List[str]) -> str:
        logger.info(f"Aggregator: Tổng hợp kết quả cho query: {query[:50]}")
        
        try:
            from src.core.brain import llm
            from langchain_core.messages import HumanMessage
            
            final_prompt = f"Bạn là một Tổng hợp viên (Aggregator). Hãy tổng hợp các dữ liệu sau để trả lời yêu cầu ban đầu một cách tự nhiên, lịch sự.\nQuy tắc: KHÔNG dùng biểu tượng cảm xúc (emoji), dùng tiếng Việt chuẩn, viết hoa đầu dòng.\nYêu cầu: {query}\n\nDữ liệu:\n" + "\n\n".join(consolidated_results)
            
            start_time = time.time()
            final_response = await llm.ainvoke([HumanMessage(content=final_prompt)])
            elapsed = time.time() - start_time
            
            logger.info(f"Aggregator: Đã tổng hợp xong trong {elapsed:.2f}s")
            return final_response.content.strip()
            
        except Exception as e:
            logger.error(f"Aggregator error: {str(e)}")
            return "Hệ thống hiện đang gặp sự cố kỹ thuật trong quá trình xử lý, rất mong bạn vui lòng thử lại sau."

aggregator_agent = AggregatorAgent()
