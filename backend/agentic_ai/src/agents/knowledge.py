from loguru import logger
from src.workflow.graph import knowledge_app


class Knowledge:
    def __init__(self):
        pass

    async def execute(self, req) -> str:
        logger.info(f"Retrieving from knowledge base for query: {req.query}")
        try:
            result = await knowledge_app.ainvoke(
                {
                    "question": req.query,
                    "user_id": req.user_id,
                    "document_ids": getattr(req, "document_ids", []),
                    "use_smart": req.useSmart,
                    "use_web": req.useWeb,
                    "chat_history": req.conversation_history or [],
                    "file_data": req.file_data,
                    "image_data": req.image_data,
                }
            )
            return result.get(
                "generation", "No relevant information found in the document"
            )
        except Exception as e:
            logger.error("Failed to retrieve from knowledge base")
            return "The system encountered an issue, please try again later"


knowledge = Knowledge()
