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
        logger.info("The user feedback was saved successfully into the system database")
        return {
            "status": "success",
            "message": "We appreciate your feedback which helps improve our artificial intelligence system",
        }
    except Exception:
        logger.error("The system failed to save the submitted user feedback")
        return {"status": "error", "message": "The system is currently unable to save your feedback please try again later"}