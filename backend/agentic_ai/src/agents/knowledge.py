from loguru import logger
from src.workflow.graph import knowledge_app


class Knowledge:
    def __init__(self):
        pass

    async def execute(self, req) -> str:
        logger.info("The system is querying the knowledge base to retrieve relevant information")
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
                "generation", "The system could not extract any relevant information from the available documents"
            )
        except Exception:
            logger.error("The system encountered an error while attempting to access the knowledge base")
            return "The system encountered an unexpected error during data retrieval and requires you to try again later"


knowledge = Knowledge()