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

class ThreadService:

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
    ):
        sender_id = str(current_user.id)
        if client_msg_id:
            existing = await MessageRepository.find_one(
                {"client_msg_id": client_msg_id, "sender_id": sender_id}
            )
            if existing:
                existing["_id"] = str(existing["_id"])
                return existing
        user_doc = await ProfileRepository.get_profile(receiver_id)
        if user_doc and sender_id in user_doc.get("blocked_users", []):
            raise Exception("Tài khoản này hiện không tiếp nhận tin nhắn từ bạn")
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
        )
        msg_dict = message.model_dump(by_alias=True)
        if reply_msg:
            msg_dict["replied_message"] = {
                "_id": reply_msg["_id"],
                "content": reply_msg.get("content"),
                "sender_id": reply_msg.get("sender_id"),
            }
        await MessageRepository.insert_one(msg_dict)
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
        return msg_dict

    @staticmethod
    @log_logic_execution
    async def get_messages(
        other_user_id: str,
        current_user,
        limit: int = Query(
            default=20, le=100
        ),
        cursor: str = None,
    ):
        if other_user_id.startswith("group_"):
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
        query = {"$text": {"$search": query_str}, "is_recalled": False}
        if other_user_id.startswith("group_"):
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
            .execute()
        )
        return messages

    @staticmethod
    @log_logic_execution
    async def forward_message(message_id: str, receiver_ids: list, current_user):
        original_msg = await MessageRepository.find_one({"_id": message_id})
        if not original_msg:
            raise ValueError("Original message not found")
        if original_msg.get("is_recalled"):
            raise ValueError("Cannot forward a recalled message")
            
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
        msg = await MessageRepository.find_one({"_id": message_id})
        if not msg:
            raise ValueError("Poll message not found")
            
        try:
            content_dict = json.loads(msg.get("content", "{}"))
            if content_dict.get("type") != "poll":
                raise ValueError("Message is not a poll")
                
            poll_data = content_dict.get("data", {})
            user_id = str(current_user.id)
            
            for opt in poll_data.get("options", []):
                if user_id in opt.get("votes", []):
                    opt["votes"].remove(user_id)
                    
            for opt in poll_data.get("options", []):
                if opt["id"] == option_id:
                    opt["votes"].append(user_id)
                    break
                    
            new_content = json.dumps({"type": "poll", "data": poll_data})
            await MessageRepository.update_one(
                {"_id": message_id},
                {"$set": {"content": new_content, "updated_at": datetime.now(timezone.utc)}}
            )
            
            # Update last_message if it's the latest
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
        except json.JSONDecodeError:
            raise ValueError("Invalid poll data format")

