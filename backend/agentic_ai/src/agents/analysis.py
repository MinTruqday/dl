from loguru import logger
from src.workflow.graph import knowledge_app


class AnalysisAgent:
    def __init__(self):
        pass

    async def execute(self, req) -> str:
        logger.info("Đang truy vấn cơ sở dữ liệu")
        try:
            if isinstance(req, dict):
                query = req.get("query", "")
                user_id = req.get("user_id", "")
                document_ids = req.get("document_ids", [])
                use_smart = req.get("use_smart", False) or req.get("useSmart", False)
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
                use_smart = getattr(req, "useSmart", False) or getattr(
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
            logger.exception(f"Lỗi truy cập cơ sở kiến thức: {e}")
            return f"Không thể lấy dữ liệu từ máy chủ, vui lòng làm mới và thử lại: {e}"


researcher = AnalysisAgent()
