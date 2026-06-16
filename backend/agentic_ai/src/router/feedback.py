from datetime import datetime, timezone
from core.config import settings
from fastapi import APIRouter
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.schemas.requests import FeedbackRequest

router = APIRouter(prefix="/phan-hoi")

@router.post("/phan-hoi")
async def submit_feedback(req: FeedbackRequest):
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client.get_default_database()
        feedback_doc = {
            "session_id": req.session_id,
            "message_id": req.message_id,
            "user_id": req.user_id,
            "vote_type": req.vote_type,
            "comment": req.comment,
            "created_at": datetime.now(timezone.utc),
        }
        await db.rag_feedback.insert_one(feedback_doc)
        client.close()
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"status": "success", "message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}
    except Exception:
        logger.error("Mất kết nối mạng tạm thời")
        return {"status": "error", "message": "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"}