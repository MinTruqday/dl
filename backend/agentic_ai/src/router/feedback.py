from datetime import datetime, timezone

from fastapi import APIRouter
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.schemas.feedback import FeedbackRequest

from core.config import settings

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
        logger.info("Lưu phản hồi thành công")
        return {
            "status": "success",
            "message": "Cảm ơn phản hồi của bạn",
        }
    except Exception:
        logger.error("Lỗi lưu phản hồi người dùng")
        return {"status": "error", "message": "Lỗi lưu phản hồi, vui lòng thử lại sau"}
