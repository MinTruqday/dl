import asyncio
import re
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.logic_logger import log_logic_execution
from src.repositories.conversation import ConversationRepository
from src.repositories.message import MessageRepository
from src.repositories.profile import ProfileRepository
from src.services.thread import ThreadService


class ConversationService:
    @staticmethod
    @log_logic_execution
    async def get_conversations(current_user):
        user_id = str(current_user.id)
        groups = await MessageRepository.find_groups({"members": user_id}).to_list(length=None)
        group_ids = [group["_id"] for group in groups]
        conversations = await (
            ConversationRepository.find(
                {
                    "$or": [
                        {"participants": user_id},
                        {"_id": {"$in": group_ids}},
                    ],
                    "cleared_by": {"$ne": user_id},
                }
            )
            .sort("updated_at", -1)
            .to_list(length=None)
        )
        other_user_ids = {
            participant
            for conversation in conversations
            if not str(conversation["_id"]).startswith("group_")
            for participant in conversation.get("participants", [])
            if participant != user_id
        }
        users = []
        if other_user_ids:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{settings.HUMANITY_URL}/nguoi-dung/hang-loat",
                        json=list(other_user_ids),
                        headers={"X-Internal-Token": settings.SECRET_KEY},
                    )
                    response.raise_for_status()
                    users = response.json().get("data", [])
            except Exception:
                logger.exception("Failed to fetch conversation participant profiles")
        user_map = {str(user["_id"]): user for user in users}
        group_map = {str(group["_id"]): group for group in groups}
        results = []
        for conversation in conversations:
            conversation_id = str(conversation["_id"])
            is_group = conversation_id.startswith("group_")
            if is_group:
                group = group_map.get(conversation_id)
                if not group:
                    continue
                other_id = conversation_id
                other_user = {
                    "username": group.get("group_name"),
                    "full_name": group.get("group_name"),
                    "avatar_url": group.get("avatar_url", ""),
                    "is_group": True,
                }
            else:
                other_id = next(
                    (
                        participant
                        for participant in conversation.get("participants", [])
                        if participant != user_id
                    ),
                    None,
                )
                if not other_id:
                    continue
                profile = user_map.get(other_id, {})
                other_user = {
                    "username": profile.get("username"),
                    "avatar_url": profile.get("avatar_url"),
                    "full_name": profile.get("full_name"),
                }
            results.append(
                {
                    "other_user_id": other_id,
                    "other_user": other_user,
                    "last_message": conversation.get("last_message"),
                    "pinned_messages": conversation.get("pinned_messages", []),
                    "unread_count": conversation.get("unread_count", {}).get(user_id, 0),
                }
            )
        return results

    @staticmethod
    @log_logic_execution
    async def delete_conversation(other_user_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            group = await MessageRepository.find_group({"_id": other_user_id})
            if not group or user_id not in group.get("members", []):
                raise HTTPException(status_code=404, detail="Không tìm thấy nhóm trò chuyện")
            if group.get("created_by") == user_id:
                await MessageRepository.delete_group({"_id": other_user_id})
                await MessageRepository.delete_many({"receiver_id": other_user_id})
                await ConversationRepository.delete_one({"_id": other_user_id})
            else:
                await MessageRepository.update_group(
                    {"_id": other_user_id},
                    {"$pull": {"members": user_id, "deputies": user_id}},
                )
                await ConversationRepository.update_one(
                    {"_id": other_user_id},
                    {"$addToSet": {"cleared_by": user_id}},
                )
            return {"status": "success"}
        await MessageRepository.update_many(
            {
                "$or": [
                    {"sender_id": user_id, "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": user_id},
                ]
            },
            {"$addToSet": {"deleted_by": user_id}},
        )
        participant_key = f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$addToSet": {"cleared_by": user_id}},
        )
        return {"status": "success"}

    @staticmethod
    @log_logic_execution
    async def mark_as_read(other_user_id: str, current_user):
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
            participant_key = other_user_id
            message_scope = {"receiver_id": other_user_id}
        else:
            participant_key = f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
            message_scope = {"receiver_id": user_id, "sender_id": other_user_id}
        delivered_scope = {**message_scope, "is_scheduled": {"$ne": True}}
        last_message = await MessageRepository.find_one(
            delivered_scope,
            sort=[("created_at", -1)],
        )
        await MessageRepository.update_many(
            {
                **delivered_scope,
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
            {**delivered_scope, "is_read": False},
            {"$set": {"is_read": True}},
        )
        update = {f"unread_count.{user_id}": 0}
        if last_message:
            update[f"last_read_message_id.{user_id}"] = last_message["_id"]
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$set": update},
        )
        return {"status": "success"}

    @staticmethod
    async def _ensure_context(other_user_id: str, current_user, allow_new_direct: bool = False):
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
        elif allow_new_direct:
            await ThreadService.ensure_target_access(other_user_id, user_id)
        else:
            if not await ProfileRepository.get_profile(other_user_id):
                raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản trò chuyện")

    @staticmethod
    def _participant_key(other_user_id: str, user_id: str) -> str:
        if other_user_id.startswith("group_"):
            return other_user_id
        return f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"

    @staticmethod
    @log_logic_execution
    async def save_draft(other_user_id: str, content: str, current_user):
        if len(content) > 10000:
            raise HTTPException(status_code=400, detail="Bản nháp vượt quá độ dài cho phép")
        await ConversationService._ensure_context(other_user_id, current_user, allow_new_direct=True)
        user_id = str(current_user.id)
        participant_key = ConversationService._participant_key(other_user_id, user_id)
        update = {"$set": {f"draft.{user_id}": content}}
        if not other_user_id.startswith("group_"):
            update["$setOnInsert"] = {"participants": sorted([user_id, other_user_id])}
        await ConversationRepository.update_one(
            {"_id": participant_key},
            update,
            upsert=True,
        )
        return {"status": "success"}

    @staticmethod
    @log_logic_execution
    async def get_draft(other_user_id: str, current_user):
        await ConversationService._ensure_context(other_user_id, current_user)
        user_id = str(current_user.id)
        conversation = await ConversationRepository.find_one(
            {"_id": ConversationService._participant_key(other_user_id, user_id)}
        )
        draft = conversation.get("draft", {}).get(user_id, "") if conversation else ""
        return {"draft": draft}

    @staticmethod
    @log_logic_execution
    async def get_conversation_settings(other_user_id: str, current_user):
        await ConversationService._ensure_context(other_user_id, current_user)
        user_id = str(current_user.id)
        participant_key = ConversationService._participant_key(other_user_id, user_id)
        settings_id = other_user_id if other_user_id.startswith("group_") else f"settings_{participant_key}"
        conversation, message_settings = await asyncio.gather(
            ConversationRepository.find_one({"_id": participant_key}),
            MessageRepository.find_setting({"_id": settings_id}),
        )
        message_settings = message_settings or {}
        conversation = conversation or {}
        return {
            "self_destruct_seconds": message_settings.get("self_destruct_seconds", 0),
            "is_muted": user_id in conversation.get("muted_by", []),
            "is_pinned": user_id in conversation.get("pinned_by", []),
            "theme": message_settings.get("theme"),
            "nicknames": message_settings.get("nicknames", {}),
            "emoji": message_settings.get("emoji"),
        }

    @staticmethod
    @log_logic_execution
    async def update_conversation_settings(other_user_id: str, updates: dict, current_user):
        await ConversationService._ensure_context(other_user_id, current_user)
        user_id = str(current_user.id)
        participant_key = ConversationService._participant_key(other_user_id, user_id)
        settings_id = other_user_id if other_user_id.startswith("group_") else f"settings_{participant_key}"
        filtered_updates = {
            key: value
            for key, value in updates.items()
            if key in {"theme", "nicknames", "emoji"}
        }
        if filtered_updates:
            await MessageRepository.update_setting(
                {"_id": settings_id},
                {"$set": filtered_updates},
                upsert=True,
            )
        return {"success": True, "message": "Cập nhật cấu hình trò chuyện thành công"}

    @staticmethod
    @log_logic_execution
    async def global_search(query: str, current_user):
        user_id = str(current_user.id)
        groups = await MessageRepository.find_groups({"members": user_id}).to_list(length=None)
        group_ids = [str(group["_id"]) for group in groups]
        match_query = {
            "content": {"$regex": re.compile(re.escape(query), re.IGNORECASE)},
            "is_recalled": False,
            "is_scheduled": {"$ne": True},
            "deleted_by": {"$ne": user_id},
            "$and": [{"$or": [{"visible_to": None}, {"visible_to": user_id}]}],
            "$or": [
                {
                    "sender_id": user_id,
                    "receiver_id": {"$not": re.compile(r"^group_")},
                },
                {"receiver_id": user_id},
                {"receiver_id": {"$in": group_ids}},
            ],
        }
        messages = await (
            MessageRepository.find(match_query)
            .sort("created_at", -1)
            .limit(50)
            .to_list(length=50)
        )
        return [
            {
                "message": message,
                "thread_id": (
                    message["receiver_id"]
                    if str(message["receiver_id"]).startswith("group_")
                    else message["receiver_id"]
                    if message["sender_id"] == user_id
                    else message["sender_id"]
                ),
                "is_group": str(message["receiver_id"]).startswith("group_"),
            }
            for message in messages
        ]

    @staticmethod
    @log_logic_execution
    async def set_quiet_hours(start_hour: int, end_hour: int, is_enabled: bool, current_user) -> dict:
        user_id = str(current_user.id)
        await MessageRepository.update_setting(
            {"_id": f"quiet_hours_{user_id}"},
            {
                "$set": {
                    "user_id": user_id,
                    "start_hour": start_hour,
                    "end_hour": end_hour,
                    "is_enabled": is_enabled,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        return {"status": "success", "start_hour": start_hour, "end_hour": end_hour, "is_enabled": is_enabled}

    @staticmethod
    @log_logic_execution
    async def set_auto_translate(target_lang: str, is_enabled: bool, current_user) -> dict:
        user_id = str(current_user.id)
        await MessageRepository.update_setting(
            {"_id": f"auto_translate_{user_id}"},
            {
                "$set": {
                    "user_id": user_id,
                    "target_lang": target_lang,
                    "is_enabled": is_enabled,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        return {"status": "success", "target_lang": target_lang, "is_enabled": is_enabled}

