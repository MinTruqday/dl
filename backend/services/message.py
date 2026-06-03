from core.database import db_client
from models.message import MessageInDB
from models.user import UserInDB
from datetime import datetime, timezone
import asyncio

class MessageService:
    @staticmethod
    async def _upsert_conversation(db, sender_id: str, receiver_id: str, message_data: dict):
        participant_key = receiver_id if receiver_id.startswith("group_") else f"{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
        
        participants = [sender_id, receiver_id] if not receiver_id.startswith("group_") else []
        
        if receiver_id.startswith("group_"):
            group_doc = await db["chat_groups"].find_one({"_id": receiver_id})
            members = group_doc.get("members", []) if group_doc else []
            inc_data = {f"unread_count.{m}": 1 for m in members if m != sender_id}
        else:
            inc_data = {f"unread_count.{receiver_id}": 1}

        update_doc = {
            "$set": {
                "last_message": message_data,
                "updated_at": datetime.now(timezone.utc),
                "cleared_by": []
            },
            "$inc": inc_data,
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc),
                "pinned_messages": []
            },
        }
        
        if not receiver_id.startswith("group_"):
            update_doc["$set"]["participants"] = sorted(participants)
            
        await db["conversations"].update_one(
            {"_id": participant_key},
            update_doc,
            upsert=True,
        )

    @staticmethod
    async def send_message(receiver_id: str, content: str, current_user, image_url: str = None, reply_to_id: str = None, audio_url: str = None, client_msg_id: str = None):
        db = db_client.mongodb.get_default_database()
        sender_id = str(current_user.id)
        
        if client_msg_id:
            existing = await db["messages"].find_one({"client_msg_id": client_msg_id, "sender_id": sender_id})
            if existing:
                existing["_id"] = str(existing["_id"])
                return existing

        user_doc = await db["users"].find_one({"_id": receiver_id}, {"blocked_users": 1})
        if user_doc and sender_id in user_doc.get("blocked_users", []):
            raise Exception("Bạn đã bị chặn bởi người dùng này.")

        self_destruct_at = None
        settings_id = f"settings_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
        
        tasks = [db["chat_settings"].find_one({"_id": settings_id})]
        if reply_to_id:
            tasks.append(db["messages"].find_one({"_id": reply_to_id}))
            
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
            self_destruct_seconds=self_destruct_seconds
        )
        msg_dict = message.model_dump(by_alias=True)
        
        if reply_msg:
            msg_dict["replied_message"] = {
                "_id": reply_msg["_id"],
                "content": reply_msg.get("content"),
                "sender_id": reply_msg.get("sender_id")
            }

        await db["messages"].insert_one(msg_dict)
        
        await MessageService._upsert_conversation(db, sender_id, receiver_id, {
            "_id": msg_dict["_id"],
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "image_url": image_url,
            "audio_url": audio_url,
            "is_recalled": False,
            "created_at": msg_dict.get("created_at", datetime.now(timezone.utc)),
        })
        return msg_dict

    @staticmethod
    async def get_messages(other_user_id: str, current_user: UserInDB, limit: int = 50, cursor: str = None):
        db = db_client.mongodb.get_default_database()
        
        if other_user_id.startswith("group_"):
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": current_user.id, "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": current_user.id}
                ]
            }

        if cursor:
            query["_id"] = {"$lt": cursor}
            
        query["deleted_by"] = {"$ne": str(current_user.id)}

        messages = await db["messages"].find(query).sort("_id", -1).limit(limit).to_list(length=limit)
        
        participant_key = other_user_id if other_user_id.startswith("group_") else f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        
        last_msg_id = messages[0]["_id"] if messages else None
        update_data = {f"unread_count.{current_user.id}": 0}
        if last_msg_id:
            update_data[f"last_read_message_id.{current_user.id}"] = last_msg_id
            
        await db["conversations"].update_one(
            {"_id": participant_key},
            {"$set": update_data}
        )

        return messages[::-1]

    @staticmethod
    async def get_conversations(current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        
        conversations = await db["conversations"].find({
            "$or": [
                {"participants": str(current_user.id)},
                {"_id": {"$in": [g["_id"] for g in await db["chat_groups"].find({"members": str(current_user.id)}).to_list(100)]}}
            ],
            "cleared_by": {"$ne": str(current_user.id)}
        }).sort("updated_at", -1).to_list(length=200)

        other_user_ids = []
        for conv in conversations:
            if not str(conv["_id"]).startswith("group_"):
                for p in conv.get("participants", []):
                    if p != str(current_user.id):
                        other_user_ids.append(p)

        users_list = await db["users"].find(
            {"_id": {"$in": other_user_ids}},
            {"username": 1, "avatar_url": 1, "full_name": 1}
        ).to_list(length=len(other_user_ids)) if other_user_ids else []
        user_map = {str(u["_id"]): u for u in users_list}

        groups_list = await db["chat_groups"].find({
            "members": str(current_user.id)
        }).to_list(length=100)
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

            if not other_id: continue

            unread = conv.get("unread_count", {}).get(str(current_user.id), 0)
            pinned_messages = conv.get("pinned_messages", [])
            
            if is_group:
                group = group_map.get(other_id)
                if group:
                    results.append({
                        "other_user_id": other_id,
                        "other_user": {
                            "username": group.get("group_name"),
                            "full_name": group.get("group_name"),
                            "avatar_url": "",
                            "is_group": True
                        },
                        "last_message": conv.get("last_message"),
                        "pinned_messages": pinned_messages,
                        "unread_count": unread
                    })
            else:
                other_user = user_map.get(other_id)
                if other_user:
                    results.append({
                        "other_user_id": other_id,
                        "other_user": {
                            "username": other_user.get("username"),
                            "avatar_url": other_user.get("avatar_url"),
                            "full_name": other_user.get("full_name")
                        },
                        "last_message": conv.get("last_message"),
                        "pinned_messages": pinned_messages,
                        "unread_count": unread
                    })

        return results

    @staticmethod
    async def toggle_pin(message_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        msg = await db["messages"].find_one({"_id": message_id})
        if not msg:
            return None
            
        participant_key = msg["receiver_id"] if msg["receiver_id"].startswith("group_") else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
        
        conv = await db["conversations"].find_one({"_id": participant_key})
        pinned_messages = conv.get("pinned_messages", []) if conv else []
        
        is_pinned = any(pm["_id"] == message_id for pm in pinned_messages)
        
        if not is_pinned and len(pinned_messages) >= 5:
            return "limit_reached"
            
        if is_pinned:
            await db["conversations"].update_one(
                {"_id": participant_key},
                {"$pull": {"pinned_messages": {"_id": message_id}}}
            )
            await db["messages"].update_one({"_id": message_id}, {"$set": {"is_pinned": False}})
        else:
            await db["conversations"].update_one(
                {"_id": participant_key},
                {"$push": {"pinned_messages": msg}}
            )
            await db["messages"].update_one({"_id": message_id}, {"$set": {"is_pinned": True}})
            
        return await db["messages"].find_one({"_id": message_id})

    @staticmethod
    async def edit_message(message_id: str, new_content: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        msg = await db["messages"].find_one({"_id": message_id})
        if not msg or msg["sender_id"] != str(current_user.id):
            return None

        await db["messages"].update_one(
            {"_id": message_id},
            {
                "$set": {
                    "content": new_content,
                    "is_edited": True,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        updated_msg = await db["messages"].find_one({"_id": message_id})
        participant_key = msg["receiver_id"] if msg["receiver_id"].startswith("group_") else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
        conv = await db["conversations"].find_one({"_id": participant_key})
        
        if conv and conv.get("last_message", {}).get("_id") == message_id:
            await db["conversations"].update_one(
                {"_id": participant_key},
                {"$set": {"last_message.content": new_content}}
            )

        if conv and any(pm["_id"] == message_id for pm in conv.get("pinned_messages", [])):
            await db["conversations"].update_one(
                {"_id": participant_key, "pinned_messages._id": message_id},
                {"$set": {"pinned_messages.$.content": new_content}}
            )
            
        return updated_msg

    @staticmethod
    async def recall_message(message_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        msg = await db["messages"].find_one({"_id": message_id})
        if not msg or msg["sender_id"] != str(current_user.id):
            return None

        recalled_content = "Tin nhắn đã bị thu hồi"

        await db["messages"].update_one(
            {"_id": message_id},
            {
                "$set": {
                    "is_recalled": True,
                    "content": recalled_content,
                    "updated_at": datetime.now(timezone.utc)
                },
                "$unset": {
                    "image_url": "",
                    "audio_url": "",
                    "file_url": "",
                    "attachments": ""
                }
            }
        )

        participant_key = msg["receiver_id"] if msg["receiver_id"].startswith("group_") else f"{min(msg['sender_id'], msg['receiver_id'])}_{max(msg['sender_id'], msg['receiver_id'])}"
        conv = await db["conversations"].find_one({"_id": participant_key})
        
        if conv and conv.get("last_message", {}).get("_id") == message_id:
            await db["conversations"].update_one(
                {"_id": participant_key},
                {"$set": {
                    "last_message.content": recalled_content,
                    "last_message.is_recalled": True,
                }, "$unset": {
                    "last_message.image_url": "",
                    "last_message.audio_url": "",
                    "last_message.file_url": ""
                }}
            )
            
        if conv and any(pm["_id"] == message_id for pm in conv.get("pinned_messages", [])):
            await db["conversations"].update_one(
                {"_id": participant_key, "pinned_messages._id": message_id},
                {"$set": {
                    "pinned_messages.$.content": recalled_content,
                    "pinned_messages.$.is_recalled": True
                }, "$unset": {
                    "pinned_messages.$.image_url": "",
                    "pinned_messages.$.audio_url": "",
                    "pinned_messages.$.file_url": ""
                }}
            )
            
        return await db["messages"].find_one({"_id": message_id})

    @staticmethod
    async def search_messages(other_user_id: str, query_str: str, current_user: UserInDB) -> list:
        db = db_client.mongodb.get_default_database()
        
        query = {
            "$text": {"$search": query_str},
            "is_recalled": False
        }
        
        if other_user_id.startswith("group_"):
            query["receiver_id"] = other_user_id
        else:
            query["$or"] = [
                {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": str(current_user.id)}
            ]
            
        messages = await db["messages"].find(query).sort("created_at", -1).to_list(length=100)
        return messages

    @staticmethod
    async def delete_conversation(other_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        if other_user_id.startswith("group_"):
            group = await db["chat_groups"].find_one({"_id": other_user_id})
            if group:
                if group.get("created_by") == str(current_user.id):
                    await db["chat_groups"].delete_one({"_id": other_user_id})
                    await db["messages"].delete_many({"receiver_id": other_user_id})
                    await db["conversations"].delete_one({"_id": other_user_id})
                else:
                    await db["chat_groups"].update_one(
                        {"_id": other_user_id},
                        {"$pull": {"members": str(current_user.id)}}
                    )
                    await db["conversations"].update_one(
                        {"_id": other_user_id},
                        {"$addToSet": {"cleared_by": str(current_user.id)}}
                    )
            return {"status": "success"}

        await db["messages"].update_many({
            "$or": [
                {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": str(current_user.id)}
            ]
        }, {"$addToSet": {"deleted_by": str(current_user.id)}})
        
        participant_key = f"{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        await db["conversations"].update_one(
            {"_id": participant_key},
            {"$addToSet": {"cleared_by": str(current_user.id)}}
        )
        return {"status": "success"}

    @staticmethod
    async def add_reaction(message_id: str, reaction: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        msg = await db["messages"].find_one({"_id": message_id})
        if not msg:
            return None

        await db["messages"].update_one(
            {"_id": message_id},
            {"$pull": {"reactions": {"user_id": str(current_user.id)}}}
        )

        if reaction:
            await db["messages"].update_one(
                {"_id": message_id},
                {"$push": {"reactions": {
                    "user_id": str(current_user.id),
                    "user_name": current_user.full_name,
                    "reaction": reaction
                }}}
            )
        return await db["messages"].find_one({"_id": message_id})

    @staticmethod
    async def mark_as_read(other_user_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        
        participant_key = other_user_id if other_user_id.startswith("group_") else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        
        last_msg = await db["messages"].find_one(
            {"receiver_id": participant_key if other_user_id.startswith("group_") else user_id},
            sort=[("created_at", -1)]
        )
        
        # update self_destruct_at for unread messages with self_destruct_seconds
        from datetime import timedelta
        await db["messages"].update_many(
            {
                "receiver_id": participant_key if other_user_id.startswith("group_") else user_id,
                "is_read": False,
                "self_destruct_seconds": {"$exists": True, "$ne": None},
                "self_destruct_at": None
            },
            [{
                "$set": {
                    "is_read": True,
                    "self_destruct_at": {
                        "$add": [datetime.now(timezone.utc), {"$multiply": ["$self_destruct_seconds", 1000]}]
                    }
                }
            }]
        )
        
        # mark others as read
        await db["messages"].update_many(
            {
                "receiver_id": participant_key if other_user_id.startswith("group_") else user_id,
                "is_read": False
            },
            {"$set": {"is_read": True}}
        )
        
        update_data = {f"unread_count.{user_id}": 0}
        if last_msg:
            update_data[f"last_read_message_id.{user_id}"] = last_msg["_id"]
            
        await db["conversations"].update_one(
            {"_id": participant_key},
            {"$set": update_data}
        )
        return {"status": "success"}

    @staticmethod
    async def share_document(receiver_id: str, document_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            return None

        content = f"Đã chia sẻ tài liệu: **[{doc.get('title')}]({document_id})**"

        message = MessageInDB(
            sender_id=str(current_user.id),
            receiver_id=receiver_id,
            content=content,
            image_url=None,
            reply_to_id=None
        )

        msg_dict = message.model_dump(by_alias=True)
        await db["messages"].insert_one(msg_dict)

        await MessageService._upsert_conversation(db, str(current_user.id), receiver_id, {
            "_id": msg_dict["_id"],
            "sender_id": str(current_user.id),
            "receiver_id": receiver_id,
            "content": content,
            "is_recalled": False,
            "created_at": msg_dict.get("created_at", datetime.now(timezone.utc)),
        })

        return msg_dict

    @staticmethod
    async def get_shared_attachments(other_user_id: str, current_user: UserInDB) -> list:
        db = db_client.mongodb.get_default_database()
        
        if other_user_id.startswith("group_"):
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": str(current_user.id)}
                ]
            }
            
        query["is_recalled"] = False
        query["$or"] = [
            {"image_url": {"$ne": None, "$ne": ""}},
            {"content": {"$regex": "Đã chia sẻ tài liệu:"}}
        ]
        
        messages = await db["messages"].find(query).sort("created_at", -1).to_list(length=100)
        attachments = []
        for m in messages:
            if m.get("image_url"):
                attachments.append({
                    "id": m["_id"],
                    "type": "image",
                    "url": m["image_url"],
                    "created_at": m["created_at"].isoformat() if isinstance(m.get("created_at"), datetime) else m.get("created_at")
                })
            else:
                attachments.append({
                    "id": m["_id"],
                    "type": "document",
                    "content": m["content"],
                    "created_at": m["created_at"].isoformat() if isinstance(m.get("created_at"), datetime) else m.get("created_at")
                })
        return attachments

    @staticmethod
    async def block_user(other_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$addToSet": {"blocked_users": other_user_id}}
        )
        return {"status": "blocked", "other_user_id": other_user_id}
