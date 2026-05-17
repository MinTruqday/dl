import time
from loguru import logger
from typing import List

class AggregatorAgent:
    def __init__(self):
        pass
        
    async def aggregate(self, query: str, consolidated_results: List[str]) -> str:
        logger.info(f"Aggregator: Consolidating results for query: {query[:50]}")
        
        try:
            from src.core.brain import llm
            from langchain_core.messages import HumanMessage
            
            final_prompt = f"Bạn là một chuyên gia tổng hợp thông tin. Hãy dựa vào các dữ liệu dưới đây để viết câu trả lời hoàn chỉnh, tự nhiên và chính xác cho yêu cầu ban đầu.\nYêu cầu: {query}\n\nDữ liệu:\n" + "\n\n".join(consolidated_results)
            
            start_time = time.time()
            final_response = await llm.ainvoke([HumanMessage(content=final_prompt)])
            elapsed = time.time() - start_time
            
            logger.info(f"Aggregator: Consolidation completed in {elapsed:.2f}s")
            return final_response.content.strip()
            
        except Exception as e:
            logger.error(f"Aggregator error: {str(e)}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

aggregator_agent = AggregatorAgent()
