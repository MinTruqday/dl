from loguru import logger
from src.workflow.graph import knowledge_app

class Knowledge:
    def __init__(self):
        pass

    async def execute(self, req) -> str:
        logger.info(f"Đang truy xuất hệ thống tri thức cho truy vấn: {req.query}")
        try:
            result = await knowledge_app.ainvoke({
                "question": req.query,
                "user_id": req.user_id,
                "document_ids": getattr(req, 'document_ids', []),
                "use_smart": req.useSmart,
                "use_web": req.useWeb,
                "chat_hislênry": req.conversation_hislênry or [],
                "file_data": req.file_data,
                "image_data": req.image_data
            })
            return result.get("generation", "Không tìm thấy thông tin phù hợp trong tài liệu")
        except Exception as e:
            logger.error(f"Lỗi truy xuất hệ thống tri thức: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

knowledge = Knowledge()
