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

class InteractionService:
    @staticmethod
    @log_logic_execution
    async def add_reaction(message_id: str, reaction: str, current_user):
        msg = await MessageRepository.find_one({"_id": message_id})
        if not msg:
            return None
        
        existing_reactions = msg.get("reactions", [])
        user_id = str(current_user.id)
        
        has_this_reaction = any(
            r.get("user_id") == user_id and r.get("reaction") == reaction
            for r in existing_reactions
        )
        
        if has_this_reaction:
            await MessageRepository.update_one(
                {"_id": message_id},
                {"$pull": {"reactions": {"user_id": user_id, "reaction": reaction}}},
            )
        elif reaction:
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
        await ProfileRepository.update_profile(str(current_user.id), {"$addToSet": {"blocked_users": other_user_id}})
        return {"status": "blocked", "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def unblock_user(other_user_id: str, current_user) -> dict:
        await ProfileRepository.update_profile(str(current_user.id), {"$pull": {"blocked_users": other_user_id}})
        return {"status": "unblocked", "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def check_blocked_status(user_id: str, other_user_id: str) -> bool:
        user_doc = await ProfileRepository.get_profile(user_id)
        other_user_doc = await ProfileRepository.get_profile(other_user_id)
        user_blocked_other = (
            other_user_id in user_doc.get("blocked_users", []) if user_doc else False
        )
        other_blocked_user = (
            user_id in other_user_doc.get("blocked_users", [])
            if other_user_doc
            else False
        )
        return user_blocked_other or other_blocked_user

    @staticmethod
    @log_logic_execution
    async def toggle_mute(other_user_id: str, current_user):
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        conv = await ConversationRepository.find_one(
            {"_id": participant_key}
        )
        muted_by = conv.get("muted_by", []) if conv else []
        is_muted = str(current_user.id) in muted_by
        if is_muted:
            await ConversationRepository.update_one(
                {"_id": participant_key}, {"$pull": {"muted_by": str(current_user.id)}}
            )
            return {"is_muted": False}
        else:
            await ConversationRepository.update_one(
                {"_id": participant_key},
                {"$addToSet": {"muted_by": str(current_user.id)}},
            )
            return {"is_muted": True}

