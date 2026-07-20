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

class ConversationService:
    @staticmethod
    @log_logic_execution
    async def get_conversations(current_user):
        conversations = (
            await ConversationRepository
            .find(
                {
                    "$or": [
                        {"participants": str(current_user.id)},
                        {
                            "_id": {
                                "$in": [
                                    g["_id"]
                                    for g in await MessageRepository.find_groups({"members": str(current_user.id)}).to_list(length=None)
                                ]
                            }
                        },
                    ],
                    "cleared_by": {"$ne": str(current_user.id)},
                }
            )
            .sort("updated_at", -1)
            .to_list(length=None)
        )
        other_user_ids = []
        for conv in conversations:
            if not str(conv["_id"]).startswith("group_"):
                for p in conv.get("participants", []):
                    if p != str(current_user.id):
                        other_user_ids.append(p)
        users_list = []
        if other_user_ids:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{settings.HUMANITY_URL}/nguoi-dung/hang-loat",
                        json=other_user_ids,
                    )
                    if resp.status_code == 200:
                        users_list = resp.json().get("data", [])
            except Exception as e:
                from loguru import logger
                logger.error(f"Error fetching users in get_conversations {e}")
        user_map = {str(u["_id"]): u for u in users_list}
        groups_list = (
            await MessageRepository.find_groups({"members": str(current_user.id)})
            .to_list(length=None)
        )
        group_map = {str(g["_id"]): g for g in groups_list}
        results = []
        for conv in conversations:
            is_group = str(conv["_id"]).startswith("group_")
            other_id = conv["_id"] if is_group else None
            if not is_group:
                for p in conv.get("participants", []):
                    if p != str(current_user.id):
                        other_id = p
                        break
            if not other_id:
                continue
            unread = conv.get("unread_count", {}).get(str(current_user.id), 0)
            pinned_messages = conv.get("pinned_messages", [])
            if is_group:
                group = group_map.get(other_id)
                if group:
                    results.append(
                        {
                            "other_user_id": other_id,
                            "other_user": {
                                "username": group.get("group_name"),
                                "full_name": group.get("group_name"),
                                "avatar_url": "",
                                "is_group": True,
                            },
                            "last_message": conv.get("last_message"),
                            "pinned_messages": pinned_messages,
                            "unread_count": unread,
                        }
                    )
            else:
                other_user = user_map.get(other_id)
                if other_user:
                    results.append(
                        {
                            "other_user_id": other_id,
                            "other_user": {
                                "username": other_user.get("username"),
                                "avatar_url": other_user.get("avatar_url"),
                                "full_name": other_user.get("full_name"),
                            },
                            "last_message": conv.get("last_message"),
                            "pinned_messages": pinned_messages,
                            "unread_count": unread,
                        }
                    )
        print(f"DEBUG: Returning {len(results)} conversations for {current_user.id}")
        return results

    @staticmethod
    @log_logic_execution
    async def delete_conversation(other_user_id: str, current_user) -> dict:
        if other_user_id.startswith("group_"):
            group = await MessageRepository.find_group(
                {"_id": other_user_id}
            )
            if group:
                if group.get("created_by") == str(current_user.id):
                    await MessageRepository.delete_group(
                        {"_id": other_user_id}
                    )
                    await MessageRepository.delete_many(
                        {"receiver_id": other_user_id}
                    )
                    await ConversationRepository.delete_one(
                        {"_id": other_user_id}
                    )
                else:
                    await MessageRepository.update_group(
                        {"_id": other_user_id},
                        {"$pull": {"members": str(current_user.id)}},
                    )
                    await ConversationRepository.update_one(
                        {"_id": other_user_id},
                        {"$addToSet": {"cleared_by": str(current_user.id)}},
                    )
            return {"status": "success"}
        await MessageRepository.update_many(
            {
                "$or": [
                    {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": str(current_user.id)},
                ]
            },
            {"$addToSet": {"deleted_by": str(current_user.id)}},
        )
        participant_key = f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$addToSet": {"cleared_by": str(current_user.id)}},
        )
        return {"status": "success"}

    @staticmethod
    @log_logic_execution
    async def mark_as_read(other_user_id: str, current_user):
        user_id = str(current_user.id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        last_msg = await MessageRepository.find_one(
            {
                "receiver_id": (
                    participant_key if other_user_id.startswith("group_") else user_id
                )
            },
            sort=[("created_at", -1)],
        )
        from datetime import timedelta

        await MessageRepository.update_many(
            {
                "receiver_id": (
                    participant_key if other_user_id.startswith("group_") else user_id
                ),
                "is_read": False,
                "self_destruct_seconds": {"$exists": True, "$ne": None},
                "self_destruct_at": None,
            },
            [
                {
                    "$set": {
                        "is_read": True,
                        "self_destruct_at": {
                            "$add": [
                                datetime.now(timezone.utc),
                                {"$multiply": ["$self_destruct_seconds", 1000]},
                            ]
                        },
                    }
                }
            ],
        )
        await MessageRepository.update_many(
            {
                "receiver_id": (
                    participant_key if other_user_id.startswith("group_") else user_id
                ),
                "is_read": False,
            },
            {"$set": {"is_read": True}},
        )
        update_data = {f"unread_count.{user_id}": 0}
        if last_msg:
            update_data[f"last_read_message_id.{user_id}"] = last_msg["_id"]
        await ConversationRepository.update_one(
            {"_id": participant_key}, {"$set": update_data}
        )
        return {"status": "success"}

    @staticmethod
    @log_logic_execution
    async def save_draft(other_user_id: str, content: str, current_user):
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$set": {f"draft.{current_user.id}": content}},
            upsert=True,
        )
        return {"status": "success"}

    @staticmethod
    @log_logic_execution
    async def get_draft(other_user_id: str, current_user):
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        conv = await ConversationRepository.find_one(
            {"_id": participant_key}
        )
        draft = conv.get("draft", {}).get(str(current_user.id), "") if conv else ""
        return {"draft": draft}

    @staticmethod
    @log_logic_execution
    async def get_conversation_settings(other_user_id: str, current_user):
        settings_id = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"settings_{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        settings = await MessageRepository.find_setting(
            {"_id": settings_id}
        )

        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        conv = await ConversationRepository.find_one(
            {"_id": participant_key}
        )
        is_muted = str(current_user.id) in conv.get("muted_by", []) if conv else False
        is_pinned = str(current_user.id) in conv.get("pinned_by", []) if conv else False

        return {
            "self_destruct_seconds": (
                settings.get("self_destruct_seconds", 0) if settings else 0
            ),
            "is_muted": is_muted,
            "is_pinned": is_pinned,
            "theme": settings.get("theme") if settings else None,
            "nicknames": settings.get("nicknames", {}) if settings else {},
            "emoji": settings.get("emoji") if settings else None,
        }

    @staticmethod
    @log_logic_execution
    async def update_conversation_settings(other_user_id: str, updates: dict, current_user):
        settings_id = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"settings_{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        allowed_keys = ["theme", "nicknames", "emoji"]
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_keys}
        if filtered_updates:
            await MessageRepository.update_setting(
                {"_id": settings_id},
                {"$set": filtered_updates},
                upsert=True
            )
        return {"success": True, "message": "Cập nhật cấu hình trò chuyện thành công"}
