from datetime import datetime, timezone
from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.repositories.conversation import ConversationRepository
from src.repositories.message import MessageRepository
from src.services.thread import ThreadService


class PrivacyService:
    @staticmethod
    @log_logic_execution
    async def toggle_self_destruct(other_user_id: str, seconds: int, current_user):
        if seconds not in {0, 10, 30, 60, 300, 3600, 86400}:
            raise HTTPException(status_code=400, detail="Thời gian tự hủy không hợp lệ")
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, str(current_user.id))
        settings_id = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"settings_{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        await MessageRepository.update_setting(
            {"_id": settings_id},
            {"$set": {"self_destruct_seconds": seconds}},
            upsert=True,
        )
        return {"self_destruct_seconds": seconds}

    @staticmethod
    @log_logic_execution
    async def set_auto_clean_schedule(other_user_id: str, days: int, current_user) -> dict:
        user_id = str(current_user.id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$set": {f"auto_clean_days.{user_id}": days}},
            upsert=True,
        )
        return {"auto_clean_days": days, "other_user_id": other_user_id}
