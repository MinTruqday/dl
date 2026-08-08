from src.core.infrastructure.redis import redis
from src.core.logic_logger import log_logic_execution
from src.repositories.message import MessageRepository
from src.repositories.conversation import ConversationRepository
from src.services.thread import ThreadService

class PinningService:
    @staticmethod
    @log_logic_execution
    async def toggle_pin(message_id: str, current_user):
        msg = await MessageRepository.find_one({"_id": message_id})
        if not msg:
            return None
        await ThreadService.ensure_message_access(msg, str(current_user.id))
        participant_key = (
            msg["receiver_id"]
            if msg["receiver_id"].startswith("group_")
            else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
        )
        lock = redis.get_client().lock(f"conversation:pin:{participant_key}", timeout=10)
        async with lock:
            conv = await ConversationRepository.find_one({"_id": participant_key})
            if not conv:
                return None
            pinned_messages = conv.get("pinned_messages", []) if conv else []
            is_pinned = any(pm.get("_id") == message_id for pm in pinned_messages)
            if not is_pinned and len(pinned_messages) >= 5:
                return "limit_reached"
            if is_pinned:
                await ConversationRepository.update_one(
                    {"_id": participant_key},
                    {"$pull": {"pinned_messages": {"_id": message_id}}},
                )
                await MessageRepository.update_one(
                    {"_id": message_id}, {"$set": {"is_pinned": False}}
                )
            else:
                await ConversationRepository.update_one(
                    {"_id": participant_key}, {"$push": {"pinned_messages": msg}}
                )
                await MessageRepository.update_one(
                    {"_id": message_id}, {"$set": {"is_pinned": True}}
                )
        return await MessageRepository.find_one({"_id": message_id})

    @staticmethod
    @log_logic_execution
    async def toggle_pin_conversation(other_user_id: str, current_user):
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
            return {"is_pinned": False}
        pinned_by = conv.get("pinned_by", []) if conv else []
        is_pinned = str(current_user.id) in pinned_by
        if is_pinned:
            await ConversationRepository.update_one(
                {"_id": participant_key}, {"$pull": {"pinned_by": str(current_user.id)}}
            )
            return {"is_pinned": False}
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$addToSet": {"pinned_by": str(current_user.id)}},
        )
        return {"is_pinned": True}

    @staticmethod
    @log_logic_execution
    async def get_pinned_messages(other_user_id: str, current_user) -> list:
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        conv = await ConversationRepository.find_one({"_id": participant_key})
        return conv.get("pinned_messages", []) if conv else []
