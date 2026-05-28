import time
from loguru import logger
from typing import List

class AggregatorAgent:
    def __init__(self):
        pass
        
    async def aggregate_stream(self, query: str, consolidated_results: List[str]):
        logger.info(f"Aggregator: Consolidating results for query: {query[:50]}")
        
        try:
            from src.core.brain import llm
            from langchain_core.messages import HumanMessage
            
            final_prompt = f"Bạn là một chuyên gia tổng hợp thông tin từ hệ thống DocLib. Hãy dựa vào các dữ liệu dưới đây để viết câu trả lời hoàn chỉnh, tự nhiên, rõ ràng và mạch lạc cho yêu cầu ban đầu. Nếu dữ liệu không đủ, hãy trả lời theo hiểu biết của bạn nhưng nói rõ là không có trong tài liệu. Đặc biệt: Tuyệt đối giữ nguyên vẹn mọi đường dẫn/link (dạng [Text](url) hoặc https://...) có trong dữ liệu và trả về cho người dùng.\nYêu cầu: {query}\n\nDữ liệu:\n" + "\n\n".join(consolidated_results)
            
            async for chunk in llm.astream([HumanMessage(content=final_prompt)]):
                if chunk.content:
                    yield chunk.content
            
        except Exception as e:
            logger.error(f"Aggregator error: {str(e)}")
            yield "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

aggregator_agent = AggregatorAgent()