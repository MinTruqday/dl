import asyncio
from datetime import datetime, timezone

from fastapi import Query
from src.schemas.chat_threads import MessageInDB

from shared.infrastructure.config import settings
from shared.infrastructure.database import db_client
from shared.repositories.base_repository import RepositoryFactory


class ChatConversation:

    @staticmethod
    async def _upsert_conversation(
        db, sender_id: str, receiver_id: str, message_data: dict
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
            group_doc = await RepositoryFactory.get("message_groups").find_one(
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
        await RepositoryFactory.get("conversations").update_one(
            {"_id": participant_key}, update_doc, upsert=True
        )

    @staticmethod
    async def send_message(
        receiver_id: str,
        content: str,
        current_user,
        image_url: str = None,
        reply_to_id: str = None,
        audio_url: str = None,
        client_msg_id: str = None,
        db=None,
    ):
        if db is None:
            db = db_client.mongodb.get_default_database()
        sender_id = str(current_user.id)
        if client_msg_id:
            existing = await RepositoryFactory.get("messages").find_one(
                {"client_msg_id": client_msg_id, "sender_id": sender_id}
            )
            if existing:
                existing["_id"] = str(existing["_id"])
                return existing
        user_doc = await RepositoryFactory.get("user_contact_profiles").find_one(
            {"_id": receiver_id}
        )
        if user_doc and sender_id in user_doc.get("blocked_users", []):
            raise Exception("Tài khoản này không nhận tin nhắn từ bạn")
        self_destruct_at = None
        settings_id = (
            f"settings_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
        )
        tasks = [
            RepositoryFactory.get("message_settings").find_one({"_id": settings_id})
        ]
        if reply_to_id:
            tasks.append(
                RepositoryFactory.get("messages").find_one({"_id": reply_to_id})
            )
        results = await asyncio.gather(*tasks)
        settings = results[0]
        reply_msg = results[1] if reply_to_id and len(results) > 1 else None
        self_destruct_seconds = None
        if settings and settings.get("self_destruct_seconds", 0) > 0:
            self_destruct_seconds = settings["self_destruct_seconds"]
        message = MessageInDB(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            image_url=image_url,
            audio_url=audio_url,
            reply_to_id=reply_to_id,
            client_msg_id=client_msg_id,
            self_destruct_seconds=self_destruct_seconds,
        )
        msg_dict = message.model_dump(by_alias=True)
        if reply_msg:
            msg_dict["replied_message"] = {
                "_id": reply_msg["_id"],
                "content": reply_msg.get("content"),
                "sender_id": reply_msg.get("sender_id"),
            }
        await RepositoryFactory.get("messages").insert_one(msg_dict)
        await ChatConversation._upsert_conversation(
            db,
            sender_id,
            receiver_id,
            {
                "_id": msg_dict["_id"],
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "content": content,
                "image_url": image_url,
                "audio_url": audio_url,
                "is_recalled": False,
                "created_at": msg_dict.get("created_at", datetime.now(timezone.utc)),
            },
        )
        return msg_dict

    @staticmethod
    async def get_messages(
        other_user_id: str,
        current_user,
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        ),
        cursor: str = None,
        db=None,
    ):
        if db is None:
            db = db_client.mongodb.get_default_database()
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
            await RepositoryFactory.get("messages")
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
        await RepositoryFactory.get("conversations").update_one(
            {"_id": participant_key}, {"$set": update_data}
        )
        return messages[::-1]

    @staticmethod
    async def get_conversations(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        conversations = (
            await RepositoryFactory.get("conversations")
            .find(
                {
                    "$or": [
                        {"participants": str(current_user.id)},
                        {
                            "_id": {
                                "$in": [
                                    g["_id"]
                                    for g in await RepositoryFactory.get(
                                        "message_groups"
                                    )
                                    .find({"members": str(current_user.id)})
                                    .to_list(100)
                                ]
                            }
                        },
                    ],
                    "cleared_by": {"$ne": str(current_user.id)},
                }
            )
            .sort("updated_at", -1)
            .to_list(length=200)
        )
        other_user_ids = []
        for conv in conversations:
            if not str(conv["_id"]).startswith("group_"):
                for p in conv.get("participants", []):
                    if p != str(current_user.id):
                        other_user_ids.append(p)
        import httpx

        users_list = []
        if other_user_ids:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{settings.ADMINISTRATION_URL}/nguoi-dung/hang-loat",
                        json=other_user_ids,
                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                    )
                    if resp.status_code == 200:
                        users_list = resp.json().get("data", [])
            except Exception:
                pass
        user_map = {str(u["_id"]): u for u in users_list}
        groups_list = (
            await RepositoryFactory.get("message_groups")
            .find({"members": str(current_user.id)})
            .to_list(length=100)
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
        return results

    @staticmethod
    async def toggle_pin(message_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        msg = await RepositoryFactory.get("messages").find_one({"_id": message_id})
        if not msg:
            return None
        participant_key = (
            msg["receiver_id"]
            if msg["receiver_id"].startswith("group_")
            else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
        )
        conv = await RepositoryFactory.get("conversations").find_one(
            {"_id": participant_key}
        )
        pinned_messages = conv.get("pinned_messages", []) if conv else []
        is_pinned = any((pm["_id"] == message_id for pm in pinned_messages))
        if not is_pinned and len(pinned_messages) >= 5:
            return "limit_reached"
        if is_pinned:
            await RepositoryFactory.get("conversations").update_one(
                {"_id": participant_key},
                {"$pull": {"pinned_messages": {"_id": message_id}}},
            )
            await RepositoryFactory.get("messages").update_one(
                {"_id": message_id}, {"$set": {"is_pinned": False}}
            )
        else:
            await RepositoryFactory.get("conversations").update_one(
                {"_id": participant_key}, {"$push": {"pinned_messages": msg}}
            )
            await RepositoryFactory.get("messages").update_one(
                {"_id": message_id}, {"$set": {"is_pinned": True}}
            )
        return await RepositoryFactory.get("messages").find_one({"_id": message_id})

    @staticmethod
    async def edit_message(message_id: str, new_content: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        msg = await RepositoryFactory.get("messages").find_one({"_id": message_id})
        if not msg or msg["sender_id"] != str(current_user.id):
            return None
        await RepositoryFactory.get("messages").update_one(
            {"_id": message_id},
            {
                "$set": {
                    "content": new_content,
                    "is_edited": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        updated_msg = await RepositoryFactory.get("messages").find_one(
            {"_id": message_id}
        )
        participant_key = (
            msg["receiver_id"]
            if msg["receiver_id"].startswith("group_")
            else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
        )
        conv = await RepositoryFactory.get("conversations").find_one(
            {"_id": participant_key}
        )
        if conv and conv.get("last_message", {}).get("_id") == message_id:
            await RepositoryFactory.get("conversations").update_one(
                {"_id": participant_key},
                {"$set": {"last_message.content": new_content}},
            )
        if conv and any(
            (pm["_id"] == message_id for pm in conv.get("pinned_messages", []))
        ):
            await RepositoryFactory.get("conversations").update_one(
                {"_id": participant_key, "pinned_messages._id": message_id},
                {"$set": {"pinned_messages.$.content": new_content}},
            )
        return updated_msg

    @staticmethod
    async def recall_message(message_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        msg = await RepositoryFactory.get("messages").find_one({"_id": message_id})
        if not msg or msg["sender_id"] != str(current_user.id):
            return None
        recalled_content = "This message has been recalled by the sender"
        await RepositoryFactory.get("messages").update_one(
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
        conv = await RepositoryFactory.get("conversations").find_one(
            {"_id": participant_key}
        )
        if conv and conv.get("last_message", {}).get("_id") == message_id:
            await RepositoryFactory.get("conversations").update_one(
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
            await RepositoryFactory.get("conversations").update_one(
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
        return await RepositoryFactory.get("messages").find_one({"_id": message_id})

    @staticmethod
    async def search_messages(
        other_user_id: str, query_str: str, current_user, db=None
    ) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        query = {"$text": {"$search": query_str}, "is_recalled": False}
        if other_user_id.startswith("group_"):
            query["receiver_id"] = other_user_id
        else:
            query["$or"] = [
                {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": str(current_user.id)},
            ]
        messages = (
            await RepositoryFactory.get("messages")
            .find(query)
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return messages

    @staticmethod
    async def delete_conversation(other_user_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        if other_user_id.startswith("group_"):
            group = await RepositoryFactory.get("message_groups").find_one(
                {"_id": other_user_id}
            )
            if group:
                if group.get("created_by") == str(current_user.id):
                    await RepositoryFactory.get("message_groups").delete_one(
                        {"_id": other_user_id}
                    )
                    await RepositoryFactory.get("messages").delete_many(
                        {"receiver_id": other_user_id}
                    )
                    await RepositoryFactory.get("conversations").delete_one(
                        {"_id": other_user_id}
                    )
                else:
                    await RepositoryFactory.get("message_groups").update_one(
                        {"_id": other_user_id},
                        {"$pull": {"members": str(current_user.id)}},
                    )
                    await RepositoryFactory.get("conversations").update_one(
                        {"_id": other_user_id},
                        {"$addToSet": {"cleared_by": str(current_user.id)}},
                    )
            return {"status": "success"}
        await RepositoryFactory.get("messages").update_many(
            {
                "$or": [
                    {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": str(current_user.id)},
                ]
            },
            {"$addToSet": {"deleted_by": str(current_user.id)}},
        )
        participant_key = f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        await RepositoryFactory.get("conversations").update_one(
            {"_id": participant_key},
            {"$addToSet": {"cleared_by": str(current_user.id)}},
        )
        return {"status": "success"}

    @staticmethod
    async def add_reaction(message_id: str, reaction: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        msg = await RepositoryFactory.get("messages").find_one({"_id": message_id})
        if not msg:
            return None
        await RepositoryFactory.get("messages").update_one(
            {"_id": message_id},
            {"$pull": {"reactions": {"user_id": str(current_user.id)}}},
        )
        if reaction:
            await RepositoryFactory.get("messages").update_one(
                {"_id": message_id},
                {
                    "$push": {
                        "reactions": {
                            "user_id": str(current_user.id),
                            "user_name": current_user.full_name,
                            "reaction": reaction,
                        }
                    }
                },
            )
        return await RepositoryFactory.get("messages").find_one({"_id": message_id})

    @staticmethod
    async def mark_as_read(other_user_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        last_msg = await RepositoryFactory.get("messages").find_one(
            {
                "receiver_id": (
                    participant_key if other_user_id.startswith("group_") else user_id
                )
            },
            sort=[("created_at", -1)],
        )
        from datetime import timedelta

        await RepositoryFactory.get("messages").update_many(
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
        await RepositoryFactory.get("messages").update_many(
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
        await RepositoryFactory.get("conversations").update_one(
            {"_id": participant_key}, {"$set": update_data}
        )
        return {"status": "success"}

    @staticmethod
    async def share_document(receiver_id: str, document_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        if not doc:
            return None
        content = f"Shared document preview and link to access {doc.get('title')} at internal reference {document_id}"
        message = MessageInDB(
            sender_id=str(current_user.id),
            receiver_id=receiver_id,
            content=content,
            image_url=None,
            reply_to_id=None,
        )
        msg_dict = message.model_dump(by_alias=True)
        await RepositoryFactory.get("messages").insert_one(msg_dict)
        await ChatConversation._upsert_conversation(
            db,
            str(current_user.id),
            receiver_id,
            {
                "_id": msg_dict["_id"],
                "sender_id": str(current_user.id),
                "receiver_id": receiver_id,
                "content": content,
                "is_recalled": False,
                "created_at": msg_dict.get("created_at", datetime.now(timezone.utc)),
            },
        )
        return msg_dict

    @staticmethod
    async def get_shared_attachments(other_user_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        if other_user_id.startswith("group_"):
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": str(current_user.id)},
                ]
            }
        query["is_recalled"] = False
        query["$or"] = [
            {"image_url": {"$ne": None, "$ne": ""}},
            {"content": {"$regex": "Shared document preview"}},
        ]
        messages = (
            await RepositoryFactory.get("messages")
            .find(query)
            .sort("created_at", -1)
            .to_list(length=100)
        )
        attachments = []
        for m in messages:
            if m.get("image_url"):
                attachments.append(
                    {
                        "id": m["_id"],
                        "type": "image",
                        "url": m["image_url"],
                        "created_at": (
                            m["created_at"].isoformat()
                            if isinstance(m.get("created_at"), datetime)
                            else m.get("created_at")
                        ),
                    }
                )
            else:
                attachments.append(
                    {
                        "id": m["_id"],
                        "type": "document",
                        "content": m["content"],
                        "created_at": (
                            m["created_at"].isoformat()
                            if isinstance(m.get("created_at"), datetime)
                            else m.get("created_at")
                        ),
                    }
                )
        return attachments

    @staticmethod
    async def block_user(other_user_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await RepositoryFactory.get("user_contact_profiles").update_one(
            {"_id": str(current_user.id)},
            {"$addToSet": {"blocked_users": other_user_id}},
            upsert=True,
        )
        return {"status": "blocked", "other_user_id": other_user_id}

    @staticmethod
    async def unblock_user(other_user_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await RepositoryFactory.get("user_contact_profiles").update_one(
            {"_id": str(current_user.id)}, {"$pull": {"blocked_users": other_user_id}}
        )
        return {"status": "unblocked", "other_user_id": other_user_id}

    @staticmethod
    async def check_blocked_status(user_id: str, other_user_id: str, db=None) -> bool:
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_doc = await RepositoryFactory.get("user_contact_profiles").find_one(
            {"_id": user_id}
        )
        other_user_doc = await RepositoryFactory.get("user_contact_profiles").find_one(
            {"_id": other_user_id}
        )
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
    async def toggle_pin_conversation(other_user_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        conv = await RepositoryFactory.get("conversations").find_one(
            {"_id": participant_key}
        )
        pinned_by = conv.get("pinned_by", []) if conv else []
        is_pinned = str(current_user.id) in pinned_by
        if is_pinned:
            await RepositoryFactory.get("conversations").update_one(
                {"_id": participant_key}, {"$pull": {"pinned_by": str(current_user.id)}}
            )
            return {"is_pinned": False}
        else:
            await RepositoryFactory.get("conversations").update_one(
                {"_id": participant_key},
                {"$addToSet": {"pinned_by": str(current_user.id)}},
            )
            return {"is_pinned": True}

    @staticmethod
    async def translate_message(
        message_id: str, target_lang: str, current_user, db=None
    ):
        if db is None:
            db = db_client.mongodb.get_default_database()
        msg = await RepositoryFactory.get("messages").find_one({"_id": message_id})
        if not msg:
            return None
        from src.core.http_client import http_client

        from shared.infrastructure.config import settings

        translated_content = ""
        try:
            response = await http_client.post(
                f"{settings.INTELLIGENCE_URL}/dich-thuat",
                json={"text": msg["content"], "target_lang": target_lang},
            )
            if response.status_code == 200:
                translated_content = response.json().get("data")
        except Exception:
            translated_content = f"Translation fallback string for {msg['content']}"
        translations = msg.get("translations", {})
        translations[target_lang] = translated_content
        await RepositoryFactory.get("messages").update_one(
            {"_id": message_id}, {"$set": {"translations": translations}}
        )
        return {
            "translated_content": translated_content,
            "target_lang": target_lang,
            "receiver_id": msg["receiver_id"],
            "sender_id": msg["sender_id"],
        }

    @staticmethod
    async def create_group(group_name: str, member_ids: list, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        from uuid6 import uuid7

        group_id = f"group_{uuid7()}"
        members = list(set(member_ids + [str(current_user.id)]))
        group_doc = {
            "_id": group_id,
            "group_name": group_name,
            "created_by": str(current_user.id),
            "members": members,
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("message_groups").insert_one(group_doc)
        return group_doc

    @staticmethod
    async def save_draft(other_user_id: str, content: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        await RepositoryFactory.get("conversations").update_one(
            {"_id": participant_key},
            {"$set": {f"drafts.{current_user.id}": content}},
            upsert=True,
        )
        return {"status": "success"}

    @staticmethod
    async def get_draft(other_user_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        conv = await RepositoryFactory.get("conversations").find_one(
            {"_id": participant_key}
        )
        draft = conv.get("drafts", {}).get(str(current_user.id), "") if conv else ""
        return {"draft": draft}

    @staticmethod
    async def toggle_self_destruct(
        other_user_id: str, seconds: int, current_user, db=None
    ):
        if db is None:
            db = db_client.mongodb.get_default_database()
        settings_id = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"settings_{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        await RepositoryFactory.get("message_settings").update_one(
            {"_id": settings_id},
            {"$set": {"self_destruct_seconds": seconds}},
            upsert=True,
        )
        return {"self_destruct_seconds": seconds}

    @staticmethod
    async def toggle_mute(other_user_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        conv = await RepositoryFactory.get("conversations").find_one(
            {"_id": participant_key}
        )
        muted_by = conv.get("muted_by", []) if conv else []
        is_muted = str(current_user.id) in muted_by
        if is_muted:
            await RepositoryFactory.get("conversations").update_one(
                {"_id": participant_key}, {"$pull": {"muted_by": str(current_user.id)}}
            )
            return {"is_muted": False}
        else:
            await RepositoryFactory.get("conversations").update_one(
                {"_id": participant_key},
                {"$addToSet": {"muted_by": str(current_user.id)}},
            )
            return {"is_muted": True}

    @staticmethod
    async def get_conversation_settings(other_user_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        settings_id = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"settings_{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        settings = await RepositoryFactory.get("message_settings").find_one(
            {"_id": settings_id}
        )

        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        conv = await RepositoryFactory.get("conversations").find_one(
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
        }
