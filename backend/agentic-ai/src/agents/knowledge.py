from loguru import logger
from src.core.knowledge import knowledge_agent_app

class KnowledgeAgent:
    def __init__(self):
        pass

    async def execute(self, req) -> str:
        logger.info(f"KnowledgeAgent: Retrieving documents for query: {req.query}")
        try:
            result = await knowledge_agent_app.ainvoke({
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
            logger.error(f"KnowledgeAgent: Retrieval failed: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

knowledge_agent = KnowledgeAgent()
