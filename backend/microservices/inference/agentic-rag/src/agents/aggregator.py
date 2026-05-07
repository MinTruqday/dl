import os
import time
from loguru import logger
from typing import Dict, Optional, List
from src.agents.router_agent import router_agent_app
class AggregatorAgent:
    def __init__(self):
        pass
    async def process_query(self, query: str, user_id: str, document_id: Optional[str] = None, 
                          conversation_id: Optional[str] = None, use_web: bool = False, use_smart: bool = False) -> Dict:
logger.info("Log message sanitized"))
        try:
            initial_state = {
                "question": query,
                "user_id": user_id,
                "document_id": document_id or "",
                "route": "",
                "final_answer": "",
                "use_web": use_web,
                "use_smart": use_smart
            }
            start_time = time.time()
            thread_id = conversation_id or user_id
            config = {"configurable": {"thread_id": thread_id}}
            final_state = router_agent_app.invoke(initial_state, config=config)
            elapsed = time.time() - start_time
            answer = final_state.get("final_answer", "DocLib không nhận được phản hồi từ hệ thống")
            route = final_state.get("route", "unknown")
logger.info("Log message sanitized"))
            return {
                "answer": answer,
                "quality_score": final_state.get("quality_score", 100) if route == "rag" else 85,
                "sources": final_state.get("sources", []), 
                "react_steps": 2 if route != "rag" else 5, 
                "elapsed_seconds": elapsed
            }
        except Exception as e:
logger.info("Log message sanitized"))
            return {
                "answer": "Hệ thống hiện đang gặp sự cố kỹ thuật trong quá trình xử lý, rất mong bạn vui lòng thử lại sau",
                "quality_score": 0,
                "sources": [],
                "react_steps": 0,
                "elapsed_seconds": 0
            }
aggregator_agent = AggregatorAgent()
