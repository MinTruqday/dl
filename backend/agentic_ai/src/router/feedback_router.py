from datetime import datetime, timezone

from core.config import settings
from fastapi import APIRouter
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.schemas.feedback_schema import FeedbackRequest

router = APIRouter(prefix="/feedback")


@router.post("/feedback")
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
        logger.info(f"Feedback saved for message {req.message_id}")
        return {
            "status": "success",
            "message": "Thank you for your feedback to help improve our AI",
        }
    except Exception as e:
        logger.error("Failed to save feedback")
        return {"status": "error", "message": "Unable to save feedback at this time"}
