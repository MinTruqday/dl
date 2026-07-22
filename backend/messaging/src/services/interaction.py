import asyncio

from fastapi import HTTPException

from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.redis import redis
from src.repositories.message import MessageRepository
from src.repositories.conversation import ConversationRepository
from src.repositories.profile import ProfileRepository
from src.services.thread import ThreadService

class InteractionService:
    @staticmethod
    @log_logic_execution
    async def add_reaction(message_id: str, reaction: str, current_user):
        msg = await MessageRepository.find_one({"_id": message_id})
        user_id = str(current_user.id)
        await ThreadService.ensure_message_access(msg, user_id)
        if not isinstance(reaction, str) or not reaction or len(reaction) > 32:
            raise HTTPException(status_code=400, detail="Cảm xúc không hợp lệ")
        lock = redis.get_client().lock(f"message:reaction:{message_id}:{user_id}", timeout=10)
        async with lock:
            msg = await MessageRepository.find_one({"_id": message_id})
            existing_reactions = msg.get("reactions", [])
            has_this_reaction = any(
                item.get("user_id") == user_id and item.get("reaction") == reaction
                for item in existing_reactions
            )
            if has_this_reaction:
                await MessageRepository.update_one(
                    {"_id": message_id},
                    {"$pull": {"reactions": {"user_id": user_id, "reaction": reaction}}},
                )
            else:
                await MessageRepository.update_one(
                    {"_id": message_id},
                    {
                        "$push": {
                            "reactions": {
                                "user_id": user_id,
                                "user_name": current_user.full_name,
                                "reaction": reaction,
                            }
                        }
                    },
                )
        return await MessageRepository.find_one({"_id": message_id})

    @staticmethod
    @log_logic_execution
    async def block_user(other_user_id: str, current_user) -> dict:
        if other_user_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Không thể tự chặn tài khoản hiện tại")
        if not await ProfileRepository.get_profile(other_user_id):
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản cần chặn")
        await MessageRepository.update_user_controls(
            str(current_user.id),
            {"$addToSet": {"blocked_users": other_user_id}},
        )
        return {"status": "blocked", "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def unblock_user(other_user_id: str, current_user) -> dict:
        await MessageRepository.update_user_controls(
            str(current_user.id),
            {"$pull": {"blocked_users": other_user_id}},
        )
        return {"status": "unblocked", "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def check_blocked_status(user_id: str, other_user_id: str) -> bool:
        user_doc, other_user_doc, user_controls, other_controls = await asyncio.gather(
            ProfileRepository.get_profile(user_id),
            ProfileRepository.get_profile(other_user_id),
            MessageRepository.get_user_controls(user_id),
            MessageRepository.get_user_controls(other_user_id),
        )
        user_blocked_other = (
            other_user_id in user_doc.get("blocked_users", []) if user_doc else False
        )
        other_blocked_user = (
            user_id in other_user_doc.get("blocked_users", [])
            if other_user_doc
            else False
        )
        local_user_block = other_user_id in (user_controls or {}).get("blocked_users", [])
        local_other_block = user_id in (other_controls or {}).get("blocked_users", [])
        return user_blocked_other or other_blocked_user or local_user_block or local_other_block

    @staticmethod
    @log_logic_execution
    async def toggle_mute(other_user_id: str, current_user):
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, str(current_user.id))
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        conv = await ConversationRepository.find_one(
            {"_id": participant_key}
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        muted_by = conv.get("muted_by", []) if conv else []
        is_muted = str(current_user.id) in muted_by
        if is_muted:
            await ConversationRepository.update_one(
                {"_id": participant_key}, {"$pull": {"muted_by": str(current_user.id)}}
            )
            return {"is_muted": False}
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$addToSet": {"muted_by": str(current_user.id)}},
        )
        return {"is_muted": True}
