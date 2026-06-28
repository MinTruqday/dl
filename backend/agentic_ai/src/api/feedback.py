from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from src.schemas.model import FeedbackRequest

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
        logger.info("Lưu phản hồi thành công")
        return {
            "status": "success",
            "message": "Cảm ơn phản hồi của bạn",
        }
    except Exception as e:
        logger.exception("Lỗi lưu trữ dữ liệu phản hồi người dùng")
        return {"status": "error", "message": f"Lỗi lưu phản hồi, vui lòng thử lại sau: {e}"}
