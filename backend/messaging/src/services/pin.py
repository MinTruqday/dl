from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import asyncio
from datetime import datetime, timezone

import httpx
from fastapi import Query
from src.schemas.thread import Record

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.message import MessageRepository
from src.repositories.conversation import ConversationRepository
from src.repositories.message import MessageRepository
from src.repositories.profile import ProfileRepository
from src.repositories.message import MessageRepository

class PinService:
    @staticmethod
    @log_logic_execution
    async def toggle_pin(message_id: str, current_user):
        msg = await MessageRepository.find_one({"_id": message_id})
        if not msg:
            return None
        participant_key = (
            msg["receiver_id"]
            if msg["receiver_id"].startswith("group_")
            else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
        )
        conv = await ConversationRepository.find_one(
            {"_id": participant_key}
        )
        pinned_messages = conv.get("pinned_messages", []) if conv else []
        is_pinned = any((pm["_id"] == message_id for pm in pinned_messages))
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
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        conv = await ConversationRepository.find_one(
            {"_id": participant_key}
        )
        pinned_by = conv.get("pinned_by", []) if conv else []
        is_pinned = str(current_user.id) in pinned_by
        if is_pinned:
            await ConversationRepository.update_one(
                {"_id": participant_key}, {"$pull": {"pinned_by": str(current_user.id)}}
            )
            return {"is_pinned": False}
        else:
            await ConversationRepository.update_one(
                {"_id": participant_key},
                {"$addToSet": {"pinned_by": str(current_user.id)}},
            )
            return {"is_pinned": True}

