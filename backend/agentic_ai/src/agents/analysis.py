from loguru import logger
from src.workflow.graph import knowledge_app

class AnalysisAgent:
    """
    <module_purpose>
    <purpose>Parses raw user requests and prepares them for execution.</purpose>
    <metis_behavior>Extracts and sanitizes metadata fields prior to dispatching to the orchestration engine.</metis_behavior>
    </module_purpose>
    """
    def __init__(self):
        pass

    async def execute(self, req) -> str:
        logger.info("Querying MongoDB")
        try:
            if isinstance(req, dict):
                query = req.get("query", "")
                user_id = req.get("user_id", "")
                document_ids = req.get("document_ids", [])
                use_smart = req.get("thinking", False) or req.get("use_smart", False)
                use_web = req.get("use_web", False) or req.get("useWeb", False)
                chat_history = req.get("chat_history", []) or req.get(
                    "conversation_history", []
                )
                file_data = req.get("file_data")
                image_data = req.get("image_data")
            else:
                query = getattr(req, "query", "")
                user_id = getattr(req, "user_id", "")
                document_ids = getattr(req, "document_ids", [])
                use_smart = getattr(req, "thinking", False) or getattr(
                    req, "use_smart", False
                )
                use_web = getattr(req, "useWeb", False) or getattr(
                    req, "use_web", False
                )
                chat_history = getattr(req, "conversation_history", []) or getattr(
                    req, "chat_history", []
                )
                file_data = getattr(req, "file_data", None)
                image_data = getattr(req, "image_data", None)

            result = await knowledge_app.ainvoke(
                {
                    "question": query,
                    "user_id": user_id,
                    "document_ids": document_ids,
                    "use_smart": use_smart,
                    "use_web": use_web,
                    "chat_history": chat_history,
                    "file_data": file_data,
                    "image_data": image_data,
                }
            )
            return result.get(
                "generation",
                "The system could not extract any relevant information from the available documents",
            )
        except Exception as e:
            logger.exception("Knowledge base access error")
            return f"Không thể kết nối đến máy chủ dữ liệu, vui lòng làm mới trang và thử lại {e}"

researcher = AnalysisAgent()
