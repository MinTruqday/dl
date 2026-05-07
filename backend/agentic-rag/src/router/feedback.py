from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings

router = APIRouter()

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    user_id: Optional[str] = "guest"
    vote_type: str = Field(..., description="Must be 'upvote', 'downvote', or 'hallucination_report'")
    comment: Optional[str] = ""

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
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.rag_feedback.insert_one(feedback_doc)
        client.close()
        logger.info(f"Feedback: Saved for message {req.message_id}")
        return {"status": "success", "message": "Cảm ơn bạn đã đóng góp ý kiến để cải thiện AI."}
    except Exception as e:
        logger.error(f"Feedback: Error saving: {e}")
        return {"status": "error", "message": "Không thể lưu ý kiến lúc này."}
