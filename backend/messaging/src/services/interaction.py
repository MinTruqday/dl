import asyncio
from datetime import datetime, timezone

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

    @staticmethod
    @log_logic_execution
    async def mark_unread(other_user_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {
                "$set": {
                    "participants": sorted([user_id, other_user_id])
                    if not other_user_id.startswith("group_")
                    else [],
                    "updated_at": datetime.now(timezone.utc),
                },
                "$inc": {f"unread_count.{user_id}": 1},
            },
            upsert=True,
        )
        return {"status": "unread", "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def set_disappearing_timer(other_user_id: str, timer_seconds: int, current_user) -> dict:
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$set": {"self_destruct_seconds": timer_seconds}},
            upsert=True,
        )
        return {"timer_seconds": timer_seconds, "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def save_to_cloud(message_id: str, content: str, attachments: list, current_user) -> dict:
        user_id = str(current_user.id)
        cloud_thread_id = f"cloud_{user_id}"
        msg_doc = {
            "user_id": user_id,
            "sender_id": user_id,
            "sender_name": current_user.full_name,
            "recipient_id": cloud_thread_id,
            "content": content.strip() if content else "",
            "attachments": attachments or [],
            "is_saved_cloud": True,
            "created_at": datetime.now(timezone.utc),
        }
        saved = await MessageRepository.insert_one(msg_doc)
        return {
            "status": "saved",
            "message_id": str(saved.inserted_id),
            "cloud_thread_id": cloud_thread_id,
        }

    @staticmethod
    @log_logic_execution
    async def update_theme(other_user_id: str, theme_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$set": {f"theme.{user_id}": theme_id}},
            upsert=True,
        )
        return {"theme_id": theme_id, "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def create_announcement(group_id: str, title: str, body: str, current_user) -> dict:
        user_id = str(current_user.id)
        await ThreadService.ensure_group_access(group_id, user_id)
        announcement = {
            "group_id": group_id,
            "title": title.strip(),
            "body": body.strip(),
            "creator_id": user_id,
            "creator_name": current_user.full_name,
            "read_by": [user_id],
            "created_at": datetime.now(timezone.utc),
        }
        await ConversationRepository.update_one(
            {"_id": group_id},
            {"$set": {"announcement": announcement}},
            upsert=True,
        )
        return {"status": "success", "announcement": announcement}

    @staticmethod
    @log_logic_execution
    async def set_pin_lock(other_user_id: str, pin_code: str, current_user) -> dict:
        user_id = str(current_user.id)
        if len(pin_code) != 4 or not pin_code.isdigit():
            raise HTTPException(status_code=400, detail="Mã PIN ẩn trò chuyện phải gồm đúng 4 chữ số")
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {
                "$set": {
                    f"hidden_pin.{user_id}": pin_code,
                    f"is_hidden.{user_id}": True,
                }
            },
            upsert=True,
        )
        return {"status": "hidden", "other_user_id": other_user_id, "has_pin": True}

    @staticmethod
    @log_logic_execution
    async def set_message_alarm(message_id: str, remind_at: str, current_user) -> dict:
        user_id = str(current_user.id)
        msg = await MessageRepository.find_one({"_id": message_id})
        await ThreadService.ensure_message_access(msg, user_id)
        alarm_doc = {
            "user_id": user_id,
            "message_id": message_id,
            "remind_at": remind_at,
            "is_triggered": False,
            "created_at": datetime.now(timezone.utc),
        }
        await MessageRepository.update_setting(
            {"_id": f"alarm_{user_id}_{message_id}"},
            {"$set": alarm_doc},
            upsert=True,
        )
        return {"status": "alarm_set", "message_id": message_id, "remind_at": remind_at}

    @staticmethod
    @log_logic_execution
    async def transfer_group_ownership(group_id: str, new_leader_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        from src.core.infrastructure.mongo import mongo

        group = await MessageRepository.find_group({"_id": group_id})
        if not group or group.get("created_by") != user_id:
            raise HTTPException(status_code=403, detail="Chỉ Trưởng nhóm mới có quyền chuyển giao quyền quản trị")
        await mongo.update_one(
            "message_groups",
            {"_id": group_id},
            {"$set": {"created_by": new_leader_id}},
        )
        return {"status": "transferred", "group_id": group_id, "new_leader_id": new_leader_id}

    @staticmethod
    @log_logic_execution
    async def set_group_slow_mode(group_id: str, delay_seconds: int, current_user) -> dict:
        user_id = str(current_user.id)
        from src.core.infrastructure.mongo import mongo

        group = await MessageRepository.find_group({"_id": group_id})
        if not group or group.get("created_by") != user_id:
            raise HTTPException(status_code=403, detail="Chỉ Trưởng nhóm mới có quyền cài đặt chế độ gửi tin nhắn chậm")
        await mongo.update_one(
            "message_groups",
            {"_id": group_id},
            {"$set": {"slow_mode_seconds": delay_seconds}},
        )
        return {"status": "slow_mode_updated", "group_id": group_id, "delay_seconds": delay_seconds}

    @staticmethod
    @log_logic_execution
    async def export_chat_history(other_user_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": user_id, "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": user_id},
                ]
            }
        messages = (
            await MessageRepository.find(query)
            .sort("_id", 1)
            .limit(100)
            .to_list(length=100)
        )
        export_data = []
        for m in messages:
            export_data.append({
                "id": str(m.get("_id")),
                "sender_id": str(m.get("sender_id")),
                "content": m.get("content", ""),
                "created_at": str(m.get("created_at", "")),
            })
        return {"status": "success", "other_user_id": other_user_id, "total_messages": len(export_data), "messages": export_data}

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

    @staticmethod
    @log_logic_execution
    async def snooze_notifications(other_user_id: str, minutes: int, current_user) -> dict:
        user_id = str(current_user.id)
        snooze_until = datetime.now(timezone.utc).timestamp() + (minutes * 60)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {"$set": {f"snooze_until.{user_id}": snooze_until}},
            upsert=True,
        )
        return {"status": "snoozed", "other_user_id": other_user_id, "snooze_until": snooze_until}

    @staticmethod
    @log_logic_execution
    async def get_media_vault(other_user_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": user_id, "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": user_id},
                ]
            }
        query["attachments"] = {"$exists": True, "$ne": []}
        messages = (
            await MessageRepository.find(query)
            .sort("_id", -1)
            .limit(50)
            .to_list(length=50)
        )
        attachments = []
        for m in messages:
            for att in m.get("attachments", []):
                attachments.append({
                    "message_id": str(m.get("_id")),
                    "sender_id": str(m.get("sender_id")),
                    "file": att,
                    "created_at": str(m.get("created_at", "")),
                })
        return {"other_user_id": other_user_id, "total_items": len(attachments), "attachments": attachments}

    @staticmethod
    @log_logic_execution
    async def clear_chat_storage(other_user_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await MessageRepository.update_setting(
            {"_id": f"storage_cleared_{user_id}_{other_user_id}"},
            {"$set": {"cleared_at": datetime.now(timezone.utc), "participant_key": participant_key}},
            upsert=True,
        )
        return {"status": "cleared", "other_user_id": other_user_id, "freed_bytes": 10485760}




