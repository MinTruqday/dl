from datetime import datetime, timezone

from src.core.infrastructure.mongo import mongo
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from loguru import logger

from src.schemas.feedback import FeedbackRequest

from src.core.dependency import CurrentUser, get_current_user

router = APIRouter(route_class=LoggingRoute, prefix="/phan-hoi")

@router.post("/phan-hoi")
async def submit_feedback(
    req: FeedbackRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Persist authenticated feedback for evaluation and future training"""
    try:
        feedback_doc = {
            "session_id": req.session_id,
            "message_id": req.message_id,
            "user_id": str(current_user.id),
            "vote_type": req.vote_type,
            "comment": req.comment,
            "created_at": datetime.now(timezone.utc),
        }

        await mongo.insert_one(collection="rag_feedback", document=feedback_doc)
        logger.info("User feedback persisted")
        return {
            "status": "success",
            "message_code": "feedback_recorded",
        }
    except Exception:
        logger.exception("User feedback persistence error")
        return {"status": "error", "error_code": "feedback_persistence_failed"}
