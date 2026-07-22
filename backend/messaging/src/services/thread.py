import asyncio
from datetime import datetime, timezone

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.logic_logger import log_logic_execution
from src.schemas.thread import Record
from src.repositories.message import MessageRepository
from src.repositories.conversation import ConversationRepository
from src.repositories.profile import ProfileRepository

class ThreadService:
    @staticmethod
    async def ensure_group_access(group_id: str, user_id: str, require_send: bool = False):
        group = await MessageRepository.find_group({"_id": group_id})
        if not group or user_id not in group.get("members", []):
            raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập nhóm trò chuyện này")
        if require_send and group.get("messaging_restricted"):
            allowed = user_id == group.get("created_by") or user_id in group.get("deputies", [])
            if not allowed:
                raise HTTPException(status_code=403, detail="Nhóm chỉ cho phép quản trị viên gửi tin nhắn")
        return group

    @staticmethod
    async def ensure_target_access(receiver_id: str, user_id: str):
        if receiver_id.startswith("group_"):
            return await ThreadService.ensure_group_access(receiver_id, user_id, require_send=True)
        if receiver_id == user_id:
            raise HTTPException(status_code=400, detail="Không thể gửi tin nhắn cho chính tài khoản hiện tại")
        sender_controls, receiver_controls, sender_profile, receiver_profile = await asyncio.gather(
            MessageRepository.get_user_controls(user_id),
            MessageRepository.get_user_controls(receiver_id),
            ProfileRepository.get_profile(user_id),
            ProfileRepository.get_profile(receiver_id),
        )
        if not receiver_profile:
            raise HTTPException(status_code=404, detail="Không tìm thấy người nhận tin nhắn")
        sender_blocked = set((sender_controls or {}).get("blocked_users", []))
        receiver_blocked = set((receiver_controls or {}).get("blocked_users", []))
        sender_blocked.update((sender_profile or {}).get("blocked_users", []))
        receiver_blocked.update(receiver_profile.get("blocked_users", []))
        if receiver_id in sender_blocked or user_id in receiver_blocked:
            raise HTTPException(status_code=403, detail="Không thể gửi tin nhắn do thiết lập chặn tài khoản")
        return None

    @staticmethod
    async def ensure_message_access(message: dict, user_id: str):
        if not message:
            raise HTTPException(status_code=404, detail="Không tìm thấy tin nhắn")
        receiver_id = str(message.get("receiver_id", ""))
        if receiver_id.startswith("group_"):
            await ThreadService.ensure_group_access(receiver_id, user_id)
        elif user_id not in {str(message.get("sender_id")), receiver_id}:
            raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập tin nhắn này")
        visible_to = message.get("visible_to")
        if visible_to is not None and user_id not in visible_to:
            raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập tin nhắn này")
        if message.get("is_scheduled") and message.get("sender_id") != user_id:
            raise HTTPException(status_code=404, detail="Không tìm thấy tin nhắn")
        return message

    @staticmethod
    def same_conversation(message: dict, sender_id: str, receiver_id: str) -> bool:
        if receiver_id.startswith("group_"):
            return message.get("receiver_id") == receiver_id
        return {str(message.get("sender_id")), str(message.get("receiver_id"))} == {
            sender_id,
            receiver_id,
        }

    @staticmethod
    @log_logic_execution
    async def _upsert_conversation(
        sender_id: str, receiver_id: str, message_data: dict
    ):
        participant_key = (
            receiver_id
            if receiver_id.startswith("group_")
            else f"{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
        )
        participants = (
            [sender_id, receiver_id] if not receiver_id.startswith("group_") else []
        )
        if receiver_id.startswith("group_"):
            group_doc = await MessageRepository.find_group(
                {"_id": receiver_id}
            )
            members = group_doc.get("members", []) if group_doc else []
            inc_data = {f"unread_count.{m}": 1 for m in members if m != sender_id}
        else:
            inc_data = {f"unread_count.{receiver_id}": 1}
        update_doc = {
            "$set": {
                "last_message": message_data,
                "updated_at": datetime.now(timezone.utc),
                "cleared_by": [],
            },
            "$inc": inc_data,
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc),
                "pinned_messages": [],
            },
        }
        if not receiver_id.startswith("group_"):
            update_doc["$set"]["participants"] = sorted(participants)
        await ConversationRepository.update_one(
            {"_id": participant_key}, update_doc, upsert=True
        )

    @staticmethod
    @log_logic_execution
    async def send_message(
        receiver_id: str,
        content: str,
        current_user,
        image_url: str = None,
        reply_to_id: str = None,
        audio_url: str = None,
        client_msg_id: str = None,
        attachments: list = None,
        parent_message_id: str = None,
        scheduled_at: datetime = None,
    ):
        sender_id = str(current_user.id)
        if not any([content and content.strip(), image_url, audio_url, attachments]):
            raise HTTPException(status_code=400, detail="Tin nhắn phải có nội dung hoặc tệp đính kèm")
        await ThreadService.ensure_target_access(receiver_id, sender_id)
        if scheduled_at:
            if scheduled_at.tzinfo is None:
                raise HTTPException(status_code=400, detail="Thời gian hẹn gửi phải có múi giờ")
            if scheduled_at <= datetime.now(timezone.utc):
                scheduled_at = None
        if client_msg_id:
            existing = await MessageRepository.find_one(
                {"client_msg_id": client_msg_id, "sender_id": sender_id}
            )
            if existing:
                existing["_id"] = str(existing["_id"])
                return existing
        self_destruct_at = None
        settings_id = (
            f"settings_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
        )
        tasks = [
            MessageRepository.find_setting({"_id": settings_id})
        ]
        if reply_to_id:
            tasks.append(
                MessageRepository.find_one({"_id": reply_to_id})
            )
        results = await asyncio.gather(*tasks)
        settings = results[0]
        reply_msg = results[1] if reply_to_id and len(results) > 1 else None
        if reply_msg:
            await ThreadService.ensure_message_access(reply_msg, sender_id)
            if not ThreadService.same_conversation(reply_msg, sender_id, receiver_id):
                raise HTTPException(status_code=400, detail="Tin nhắn trả lời không thuộc cuộc trò chuyện này")
        if parent_message_id:
            parent = await MessageRepository.find_one({"_id": parent_message_id})
            await ThreadService.ensure_message_access(parent, sender_id)
            if not ThreadService.same_conversation(parent, sender_id, receiver_id):
                raise HTTPException(status_code=400, detail="Tin nhắn gốc không thuộc cuộc trò chuyện này")
        self_destruct_seconds = None
        if settings and settings.get("self_destruct_seconds", 0) > 0:
            self_destruct_seconds = settings["self_destruct_seconds"]
        message = Record(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            image_url=image_url,
            audio_url=audio_url,
            reply_to_id=reply_to_id,
            client_msg_id=client_msg_id,
            self_destruct_seconds=self_destruct_seconds,
            attachments=attachments or [],
            parent_message_id=parent_message_id,
            scheduled_at=scheduled_at,
            is_scheduled=True if scheduled_at and scheduled_at > datetime.now(timezone.utc) else False,
        )
        msg_dict = message.model_dump(by_alias=True)
        if reply_msg:
            msg_dict["replied_message"] = {
                "_id": reply_msg["_id"],
                "content": reply_msg.get("content"),
                "sender_id": reply_msg.get("sender_id"),
            }
        try:
            await MessageRepository.insert_one(msg_dict)
        except DuplicateKeyError:
            if not client_msg_id:
                raise
            existing = await MessageRepository.find_one(
                {"client_msg_id": client_msg_id, "sender_id": sender_id}
            )
            if existing:
                return existing
            raise

        if not msg_dict["is_scheduled"]:
            await ThreadService._upsert_conversation(
                sender_id,
                receiver_id,
                {
                    "_id": msg_dict["_id"],
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "content": content,
                    "image_url": image_url,
                    "audio_url": audio_url,
                    "attachments": attachments or [],
                    "is_recalled": False,
                    "created_at": msg_dict.get("created_at", datetime.now(timezone.utc)),
                },
            )
            if parent_message_id:
                await MessageRepository.update_one(
                    {"_id": parent_message_id},
                    {"$inc": {"thread_count": 1}}
                )
        return msg_dict

    @staticmethod
    @log_logic_execution
    async def get_thread_replies(
        parent_message_id: str,
        current_user,
        limit: int = 20,
        cursor: str = None,
    ):
        user_id = str(current_user.id)
        parent = await MessageRepository.find_one({"_id": parent_message_id})
        await ThreadService.ensure_message_access(parent, user_id)
        query = {
            "parent_message_id": parent_message_id,
            "deleted_by": {"$ne": user_id},
            "is_scheduled": {"$ne": True},
            "$or": [{"visible_to": None}, {"visible_to": user_id}],
        }
        if cursor:
            query["_id"] = {"$lt": cursor}
        
        messages = (
            await MessageRepository
            .find(query)
            .sort("created_at", -1)
            .limit(limit)
            .to_list(length=limit)
        )
        return messages[::-1]

    @staticmethod
    @log_logic_execution
    async def get_messages(
        other_user_id: str,
        current_user,
        limit: int = 20,
        cursor: str = None,
    ):
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, str(current_user.id))
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": current_user.id, "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": current_user.id},
                ]
            }
        if cursor:
            query["_id"] = {"$lt": cursor}
        query["deleted_by"] = {"$ne": str(current_user.id)}
        query["is_scheduled"] = {"$ne": True}
        query["$and"] = [
            {"$or": [{"visible_to": None}, {"visible_to": str(current_user.id)}]}
        ]
        messages = (
            await MessageRepository
            .find(query)
            .sort("_id", -1)
            .limit(limit)
            .to_list(length=limit)
        )
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        last_msg_id = messages[0]["_id"] if messages else None
        update_data = {f"unread_count.{current_user.id}": 0}
        if last_msg_id:
            update_data[f"last_read_message_id.{current_user.id}"] = last_msg_id
        await ConversationRepository.update_one(
            {"_id": participant_key}, {"$set": update_data}
        )
        return messages[::-1]

    @staticmethod
    @log_logic_execution
    async def edit_message(message_id: str, new_content: str, current_user):
        msg = await MessageRepository.find_one({"_id": message_id})
        if not msg or msg["sender_id"] != str(current_user.id):
            return None
        await MessageRepository.update_one(
            {"_id": message_id},
            {
                "$set": {
                    "content": new_content,
                    "is_edited": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        updated_msg = await MessageRepository.find_one(
            {"_id": message_id}
        )
        participant_key = (
            msg["receiver_id"]
            if msg["receiver_id"].startswith("group_")
            else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
        )
        conv = await ConversationRepository.find_one(
            {"_id": participant_key}
        )
        if conv and conv.get("last_message", {}).get("_id") == message_id:
            await ConversationRepository.update_one(
                {"_id": participant_key},
                {"$set": {"last_message.content": new_content}},
            )
        if conv and any(
            (pm["_id"] == message_id for pm in conv.get("pinned_messages", []))
        ):
            await ConversationRepository.update_one(
                {"_id": participant_key, "pinned_messages._id": message_id},
                {"$set": {"pinned_messages.$.content": new_content}},
            )
        return updated_msg

    @staticmethod
    @log_logic_execution
    async def recall_message(message_id: str, current_user):
        msg = await MessageRepository.find_one({"_id": message_id})
        if not msg or msg["sender_id"] != str(current_user.id):
            return None
        recalled_content = "This message has been recalled by the sender"
        await MessageRepository.update_one(
            {"_id": message_id},
            {
                "$set": {
                    "is_recalled": True,
                    "content": recalled_content,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$unset": {
                    "image_url": "",
                    "audio_url": "",
                    "file_url": "",
                    "attachments": "",
                },
            },
        )
        participant_key = (
            msg["receiver_id"]
            if msg["receiver_id"].startswith("group_")
            else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
        )
        conv = await ConversationRepository.find_one(
            {"_id": participant_key}
        )
        if conv and conv.get("last_message", {}).get("_id") == message_id:
            await ConversationRepository.update_one(
                {"_id": participant_key},
                {
                    "$set": {
                        "last_message.content": recalled_content,
                        "last_message.is_recalled": True,
                    },
                    "$unset": {
                        "last_message.image_url": "",
                        "last_message.audio_url": "",
                        "last_message.file_url": "",
                    },
                },
            )
        if conv and any(
            (pm["_id"] == message_id for pm in conv.get("pinned_messages", []))
        ):
            await ConversationRepository.update_one(
                {"_id": participant_key, "pinned_messages._id": message_id},
                {
                    "$set": {
                        "pinned_messages.$.content": recalled_content,
                        "pinned_messages.$.is_recalled": True,
                    },
                    "$unset": {
                        "pinned_messages.$.image_url": "",
                        "pinned_messages.$.audio_url": "",
                        "pinned_messages.$.file_url": "",
                    },
                },
            )
        return await MessageRepository.find_one({"_id": message_id})

    @staticmethod
    @log_logic_execution
    async def search_messages(
        other_user_id: str, query_str: str, current_user
    ) -> list:
        user_id = str(current_user.id)
        query = {
            "$text": {"$search": query_str},
            "is_recalled": False,
            "is_scheduled": {"$ne": True},
            "deleted_by": {"$ne": user_id},
            "$and": [{"$or": [{"visible_to": None}, {"visible_to": user_id}]}],
        }
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
            query["receiver_id"] = other_user_id
        else:
            query["$or"] = [
                {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": str(current_user.id)},
            ]
        messages = (
            await MessageRepository
            .find(query)
            .sort("created_at", -1)
            .to_list(length=None)
        )
        return messages

    @staticmethod
    @log_logic_execution
    async def forward_message(message_id: str, receiver_ids: list, current_user):
        original_msg = await MessageRepository.find_one({"_id": message_id})
        await ThreadService.ensure_message_access(original_msg, str(current_user.id))
        if original_msg.get("is_recalled"):
            raise HTTPException(status_code=400, detail="Không thể chuyển tiếp tin nhắn đã thu hồi")
            
        forwarded_messages = []
        for receiver_id in receiver_ids:
            msg = await ThreadService.send_message(
                receiver_id=receiver_id,
                content=original_msg.get("content", ""),
                current_user=current_user,
                image_url=original_msg.get("image_url"),
                audio_url=original_msg.get("audio_url"),
                attachments=original_msg.get("attachments", [])
            )
            forwarded_messages.append(msg)
        return {"success": True, "messages": forwarded_messages}

    @staticmethod
    @log_logic_execution
    async def create_poll(receiver_id: str, question: str, options: list, current_user):
        import json
        poll_data = {
            "question": question,
            "options": [{"id": f"opt_{i}", "text": opt, "votes": []} for i, opt in enumerate(options)]
        }
        return await ThreadService.send_message(
            receiver_id=receiver_id,
            content=json.dumps({"type": "poll", "data": poll_data}),
            current_user=current_user
        )

    @staticmethod
    @log_logic_execution
    async def vote_poll(message_id: str, option_id: str, current_user):
        import json
        from src.core.infrastructure.redis import redis

        lock = redis.get_client().lock(f"message:poll:{message_id}", timeout=10)
        async with lock:
            msg = await MessageRepository.find_one({"_id": message_id})
            await ThreadService.ensure_message_access(msg, str(current_user.id))
            try:
                content_dict = json.loads(msg.get("content", "{}"))
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Dữ liệu bình chọn không hợp lệ")
            if content_dict.get("type") != "poll":
                raise HTTPException(status_code=400, detail="Tin nhắn không phải là bình chọn")
            poll_data = content_dict.get("data", {})
            options = poll_data.get("options", [])
            if not any(option.get("id") == option_id for option in options):
                raise HTTPException(status_code=400, detail="Lựa chọn bình chọn không tồn tại")
            user_id = str(current_user.id)
            for option in options:
                votes = option.setdefault("votes", [])
                if user_id in votes:
                    votes.remove(user_id)
            for option in options:
                if option.get("id") == option_id:
                    option["votes"].append(user_id)
                    break
            new_content = json.dumps({"type": "poll", "data": poll_data})
            await MessageRepository.update_one(
                {"_id": message_id},
                {"$set": {"content": new_content, "updated_at": datetime.now(timezone.utc)}},
            )
            participant_key = (
                msg["receiver_id"]
                if msg["receiver_id"].startswith("group_")
                else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
            )
            conv = await ConversationRepository.find_one({"_id": participant_key})
            if conv and conv.get("last_message", {}).get("_id") == message_id:
                await ConversationRepository.update_one(
                    {"_id": participant_key},
                    {"$set": {"last_message.content": new_content}},
                )
            return await MessageRepository.find_one({"_id": message_id})

    @staticmethod
    @log_logic_execution
    async def process_scheduled_messages():
        from src.api.thread import publish_personal_message
        now = datetime.now(timezone.utc)
        query = {
            "is_scheduled": True,
            "scheduled_at": {"$lte": now}
        }
        messages = await MessageRepository.find(query).sort("scheduled_at", 1).limit(100).to_list(length=100)

        for msg in messages:
            msg_id = msg["_id"]
            claimed = await MessageRepository.claim_scheduled_message(msg_id, now)
            if not claimed:
                continue
            msg = claimed
            sender_id = msg["sender_id"]
            receiver_id = msg["receiver_id"]
            await ThreadService._upsert_conversation(
                sender_id,
                receiver_id,
                {
                    "_id": msg_id,
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "content": msg.get("content"),
                    "image_url": msg.get("image_url"),
                    "audio_url": msg.get("audio_url"),
                    "attachments": msg.get("attachments", []),
                    "is_recalled": False,
                    "created_at": now,
                },
            )
            
            await publish_personal_message(
                {"type": "new_message", "data": msg}, receiver_id
            )
            await publish_personal_message(
                {"type": "message_sent_ack", "data": msg}, sender_id
            )
