from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from src.schemas.feedback import FeedbackRequest

from src.core.infrastructure.configuration import settings

router = APIRouter(route_class=LoggingRoute, prefix="/phan-hoi")

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

        await mongo.insert_one(collection="rag_feedback", document=feedback_doc)
        client.close()
        logger.info("User feedback persisted successfully")
        return {
            "status": "success",
            "message": "Chân thành cảm ơn phản hồi đóng góp của bạn",
        }
    except Exception as e:
        logger.exception("User feedback persistence error")
        return {"status": "error", "message": f"Hệ thống không thể ghi nhận phản hồi vào lúc này, vui lòng thử lại sau {e}"}
