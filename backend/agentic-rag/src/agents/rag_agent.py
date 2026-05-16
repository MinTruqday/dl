from loguru import logger
from src.agents.core_rag import rag_agent_app

class RAGAgent:
    def __init__(self):
        pass

    async def execute(self, req) -> str:
        logger.info(f"RAGAgent: Truy xuất tài liệu cho truy vấn: {req.query}")
        try:
            result = await rag_agent_app.ainvoke({
                "question": req.query,
                "user_id": req.user_id,
                "document_id": req.document_id,
                "use_smart": req.useSmart,
                "use_web": req.useWeb,
                "chat_history": req.conversation_history or [],
                "file_data": req.file_data,
                "image_data": req.image_data
            })
            return result.get("generation", "Không tìm thấy thông tin phù hợp trong tài liệu.")
        except Exception as e:
            logger.error(f"RAGAgent: Lỗi truy xuất: {e}")
            return "Hệ thống gặp sự cố khi đọc tài liệu nội bộ."

rag_agent = RAGAgent()
