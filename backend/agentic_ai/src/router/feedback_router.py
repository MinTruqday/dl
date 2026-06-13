from datetime import datetime, timezone

from core.config import settings
from fastapi import APIRouter
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.schemas.feedback_schema import FeedbackRequest

router = APIRouter(prefix="/phan-hoi")


@router.post("/phan-hoi")
async def submit_feedback(req: FeedbackRequest):
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client.doclib

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
        logger.info(f"Đã lưu đánh giá cho tin nhắn {req.message_id}")
        return {
            "status": "success",
            "message": "Cảm ơn bạn đã đóng góp ý kiến để cải thiện AI",
        }
    except Exception as e:
        logger.error("Lỗi lưu đánh giá")
        return {"status": "error", "message": "Không thể lưu ý kiến lúc này"}
