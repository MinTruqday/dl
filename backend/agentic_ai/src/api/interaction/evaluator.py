from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.dependency import CurrentUser, get_current_user
from src.schemas.interaction import UserInstructionsRequest
from src.services.workspace import workspace

router = APIRouter()

@router.get("/khong-gian/{session_id}")
async def get_workspace(session_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """Return the authenticated user's workspace state for one conversation."""
    row = await workspace.get(session_id, str(current_user.id))
    if not row:
        return {"status": "success", "data": None}
    return {"status": "success", "data": row}

@router.get("/tuy-chon-ca-nhan")
async def get_user_instructions(current_user: CurrentUser = Depends(get_current_user)):
    """Return the authenticated user's personal assistant instructions."""
    user_id = str(current_user.id)
    db = database.mongodb[settings.AGENTIC_AI_DB_NAME]
    doc = await db.user_instructions.find_one({"_id": user_id})
    instructions = doc.get("instructions", "") if doc else ""
    return {"status": "success", "data": {"instructions": instructions}}

@router.post("/tuy-chon-ca-nhan")
async def save_user_instructions(
    req: UserInstructionsRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Save the authenticated user's personal assistant instructions."""
    user_id = str(current_user.id)
    instructions = req.instructions.strip()
    db = database.mongodb[settings.AGENTIC_AI_DB_NAME]
    await db.user_instructions.update_one(
        {"_id": user_id},
        {"$set": {"instructions": instructions, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return {
        "status": "success",
        "message_code": "user_instructions_updated",
        "data": {"instructions": instructions},
    }

@router.delete("/tuy-chon-ca-nhan")
async def clear_user_instructions(current_user: CurrentUser = Depends(get_current_user)):
    """Clear the authenticated user's personal assistant instructions."""
    user_id = str(current_user.id)
    db = database.mongodb[settings.AGENTIC_AI_DB_NAME]
    await db.user_instructions.delete_one({"_id": user_id})
    return {"status": "success", "message_code": "user_instructions_cleared"}
