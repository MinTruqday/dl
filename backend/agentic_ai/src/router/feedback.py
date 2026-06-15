from datetime import datetime, timezone
from core.config import settings
from fastapi import APIRouter
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.schemas.requests import FeedbackRequest

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
        logger.info("The submitted analytical user qualitative interaction evaluation feedback was firmly saved safely operational internal memory")
        return {"status": "success", "message": "We highly appreciate insightful comprehensive functional evaluation assisting artificial intelligence systemic framework improvement capabilities directly"}
    except Exception:
        logger.error("The network logging operational pipeline utterly failed accurately recording user submitted interactive structural textual feedback")
        return {"status": "error", "message": "The system encountered an unexpected error and requires you to try again later"}