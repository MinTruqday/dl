from core.database import db_client
from models.chat import MessageInDB, MessageCreate
from models.user import UserInDB
from datetime import datetime, timezone
from typing import List

class ChatService:
    @staticmethod
    async def send_message(receiver_id: str, content: str, current_user: UserInDB, image_url: str = None, reply_to_id: str = None, audio_url: str = None):
        db = db_client.mongodb.get_default_database()
        
        self_destruct_at = None
        settings_id = f"settings_{min(str(current_user.id), receiver_id)}_{max(str(current_user.id), receiver_id)}"
        settings = await db["chat_settings"].find_one({"_id": settings_id})
        if settings and settings.get("self_destruct_seconds", 0) > 0:
            from datetime import timedelta
            self_destruct_at = datetime.now(timezone.utc) + timedelta(seconds=settings["self_destruct_seconds"])

        message = MessageInDB(
            sender_id=str(current_user.id),
            receiver_id=receiver_id,
            content=content,
            image_url=image_url,
            audio_url=audio_url,
            reply_to_id=reply_to_id,
            self_destruct_at=self_destruct_at
        )
        await db["messages"].insert_one(message.model_dump(by_alias=True))
        res_data = message.model_dump(by_alias=True)
        if reply_to_id:
            res_data["replied_message"] = await db["messages"].find_one({"_id": reply_to_id})
            
        return res_data

    @staticmethod
    async def get_messages(other_user_id: str, current_user: UserInDB, limit: int = 50, cursor: str = None):
        query = {
            "$and": [
                {
                    "$or": [
                        {"sender_id": current_user.id, "receiver_id": other_user_id},
                        {"sender_id": other_user_id, "receiver_id": current_user.id}
                    ]
                },
                {
                    "$or": [
                        {"self_destruct_at": None},
                        {"self_destruct_at": {"$gt": datetime.now(timezone.utc)}}
                    ]
                }
            ]
        }
        
        if cursor:
            query["created_at"] = {"$lt": datetime.fromisoformat(cursor.replace('Z', '+00:00'))}
            
        db = db_client.mongodb.get_default_database()
        cursor_query = db["messages"].find(query).sort("created_at", -1).limit(limit)
        messages = await cursor_query.to_list(length=limit)
        
        reply_ids = [msg["reply_to_id"] for msg in messages if msg.get("reply_to_id")]
        if reply_ids:
            replied_msgs = await db["messages"].find({"_id": {"$in": reply_ids}}).to_list(length=len(reply_ids))
            reply_map = {str(r["_id"]): r for r in replied_msgs}
            for msg in messages:
                if msg.get("reply_to_id"):
                    msg["replied_message"] = reply_map.get(msg["reply_to_id"])
        
        await db["messages"].update_many(
            {"sender_id": other_user_id, "receiver_id": current_user.id, "is_read": False},
            {"$set": {"is_read": True}}
        )
        
        return messages[::-1]

    @staticmethod
    async def toggle_pin(message_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        msg = await db["messages"].find_one({"_id": message_id})
        if not msg:
            return None
        if msg["sender_id"] != current_user.id and msg["receiver_id"] != current_user.id:
            return None
            
        new_state = not msg.get("is_pinned", False)
        
        if new_state:
            query_pinned = {
                "$or": [
                    {"sender_id": current_user.id, "receiver_id": msg["receiver_id"]},
                    {"sender_id": msg["receiver_id"], "receiver_id": current_user.id}
                ],
                "is_pinned": True
            }
            pinned_count = await db["messages"].count_documents(query_pinned)
            if pinned_count >= 3:
                return "limit_reached"

        await db["messages"].update_one({"_id": message_id}, {"$set": {"is_pinned": new_state}})
        return await db["messages"].find_one({"_id": message_id})

    @staticmethod
    async def edit_message(message_id: str, new_content: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        msg = await db["messages"].find_one({"_id": message_id})
        if not msg or msg["sender_id"] != current_user.id:
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
        return await db["messages"].find_one({"_id": message_id})

    @staticmethod
    async def get_conversations(current_user: UserInDB):
        pipeline = [
            {
                "$match": {
                    "$or": [{"sender_id": current_user.id}, {"receiver_id": current_user.id}]
                }
            },
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": {
                        "$cond": [
                            {"$eq": ["$sender_id", current_user.id]},
                            "$receiver_id",
                            "$sender_id"
                        ]
                    },
                    "last_message": {"$first": "$$ROOT"},
                    "unread_count": {
                        "$sum": {
                            "$cond": [
                                {"$and": [{"$eq": ["$receiver_id", current_user.id]}, {"$eq": ["$is_read", False]}]},
                                1,
                                0
                            ]
                        }
                    }
                }
            }
        ]
        
        db = db_client.mongodb.get_default_database()
        conversations = await db["messages"].aggregate(pipeline).to_list(length=100)
        
        other_user_ids = [conv["_id"] for conv in conversations]

        users_list = await db["users"].find({"_id": {"$in": other_user_ids}}, {"username": 1, "avatar_url": 1, "full_name": 1}).to_list(length=len(other_user_ids)) if other_user_ids else []
        user_map = {str(u["_id"]): u for u in users_list}

        groups_list = await db["chat_groups"].find({"_id": {"$in": other_user_ids}}).to_list(length=len(other_user_ids)) if other_user_ids else []
        group_map = {str(g["_id"]): g for g in groups_list}

        pinned_query = {
            "$or": [],
            "is_pinned": True
        }
        for uid in other_user_ids:
            pinned_query["$or"].append({"sender_id": current_user.id, "receiver_id": uid})
            pinned_query["$or"].append({"sender_id": uid, "receiver_id": current_user.id})
        
        all_pinned = await db["messages"].find(pinned_query).sort("created_at", -1).to_list(length=500) if other_user_ids else []
        pinned_map = {}
        for pm in all_pinned:
            key = pm["receiver_id"] if pm["sender_id"] == current_user.id else pm["sender_id"]
            pinned_map.setdefault(key, [])
            if len(pinned_map[key]) < 5:
                pinned_map[key].append(pm)

        results = []
        for conv in conversations:
            other_user = user_map.get(conv["_id"])
            group = group_map.get(conv["_id"])
            if other_user:
                results.append({
                    "other_user_id": conv["_id"],
                    "other_user": {
                        "username": other_user.get("username"),
                        "avatar_url": other_user.get("avatar_url"),
                        "full_name": other_user.get("full_name")
                    },
                    "last_message": conv["last_message"],
                    "pinned_messages": pinned_map.get(conv["_id"], []),
                    "unread_count": conv["unread_count"]
                })
            elif group:
                results.append({
                    "other_user_id": conv["_id"],
                    "other_user": {
                        "username": group.get("group_name"),
                        "full_name": group.get("group_name"),
                        "avatar_url": "",
                        "is_group": True
                    },
                    "last_message": conv["last_message"],
                    "pinned_messages": pinned_map.get(conv["_id"], []),
                    "unread_count": conv["unread_count"]
                })
                
        empty_groups = await db["chat_groups"].find({
            "members": str(current_user.id),
            "_id": {"$nin": other_user_ids}
        }).to_list(length=100)
        
        for eg in empty_groups:
            results.append({
                "other_user_id": eg["_id"],
                "other_user": {
                    "username": eg.get("group_name"),
                    "full_name": eg.get("group_name"),
                    "avatar_url": "",
                    "is_group": True
                },
                "last_message": None,
                "pinned_messages": [],
                "unread_count": 0
            })

        return results

    @staticmethod
    async def recall_message(message_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        msg = await db["messages"].find_one({"_id": message_id})
        if not msg or msg["sender_id"] != current_user.id:
            return None
            
        await db["messages"].update_one(
            {"_id": message_id},
            {
                "$set": {
                    "is_recalled": True,
                    "content": "Tin nhắn đã bị thu hồi",
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return await db["messages"].find_one({"_id": message_id})

    @staticmethod
    async def search_messages(other_user_id: str, query_str: str, current_user: UserInDB) -> list:
        db = db_client.mongodb.get_default_database()
        query = {
            "$or": [
                {"sender_id": current_user.id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": current_user.id}
            ],
            "content": {"$regex": query_str, "$options": "i"},
            "is_recalled": False
        }
        messages = await db["messages"].find(query).sort("created_at", -1).to_list(length=100)
        return messages[::-1]

    @staticmethod
    async def delete_conversation(other_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        if other_user_id.startswith("group_"):
            group = await db["chat_groups"].find_one({"_id": other_user_id})
            if group:
                if group.get("created_by") == str(current_user.id):
                    await db["chat_groups"].delete_one({"_id": other_user_id})
                    await db["messages"].delete_many({"receiver_id": other_user_id})
                else:
                    await db["chat_groups"].update_one(
                        {"_id": other_user_id},
                        {"$pull": {"members": str(current_user.id)}}
                    )
            return {"status": "success"}
            
        await db["messages"].delete_many({
            "$or": [
                {"sender_id": current_user.id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": current_user.id}
            ]
        })
        return {"status": "success"}

    @staticmethod
    async def add_reaction(message_id: str, reaction: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        msg = await db["messages"].find_one({"_id": message_id})
        if not msg:
            return None
            
        reactions = msg.get("reactions", [])
        updated_reactions = [r for r in reactions if r["user_id"] != current_user.id]
        
        if reaction:
            updated_reactions.append({
                "user_id": current_user.id,
                "user_name": current_user.full_name,
                "reaction": reaction
            })
            
        await db["messages"].update_one(
            {"_id": message_id},
            {"$set": {"reactions": updated_reactions}}
        )
        return await db["messages"].find_one({"_id": message_id})

    @staticmethod
    async def mark_as_read(other_user_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        await db["messages"].update_many(
            {"sender_id": other_user_id, "receiver_id": current_user.id, "is_read": False},
            {"$set": {"is_read": True}}
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
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content,
            image_url=None,
            reply_to_id=None
        )
        await db["messages"].insert_one(message.model_dump(by_alias=True))
        return message.model_dump(by_alias=True)

    @staticmethod
    async def get_shared_attachments(other_user_id: str, current_user: UserInDB) -> list:
        db = db_client.mongodb.get_default_database()
        query = {
            "$or": [
                {"sender_id": current_user.id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": current_user.id}
            ],
            "is_recalled": False,
            "$or": [
                {"image_url": {"$ne": None, "$ne": ""}},
                {"content": {"$regex": "Đã chia sẻ tài liệu:"}}
            ]
        }
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

    @staticmethod
    async def unblock_user(other_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$pull": {"blocked_users": other_user_id}}
        )
        return {"status": "unblocked", "other_user_id": other_user_id}

    @staticmethod
    async def check_blocked_status(user_a: str, user_b: str) -> bool:
        db = db_client.mongodb.get_default_database()
        ua = await db["users"].find_one({"_id": user_a})
        ub = await db["users"].find_one({"_id": user_b})
        
        if ua and user_b in ua.get("blocked_users", []):
            return True
        if ub and user_a in ub.get("blocked_users", []):
            return True
        return False

    @staticmethod
    async def toggle_pin_conversation(other_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        user_data = await db["users"].find_one({"_id": str(current_user.id)})
        pinned = user_data.get("pinned_conversations", [])
        
        if other_user_id in pinned:
            await db["users"].update_one(
                {"_id": str(current_user.id)},
                {"$pull": {"pinned_conversations": other_user_id}}
            )
            return {"is_pinned": False}
        else:
            await db["users"].update_one(
                {"_id": str(current_user.id)},
                {"$addToSet": {"pinned_conversations": other_user_id}}
            )
            return {"is_pinned": True}

    @staticmethod
    async def translate_message(message_id: str, target_lang: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        msg = await db["messages"].find_one({"_id": message_id})
        if not msg:
            return None
            
        content = msg.get("content", "")
        
        translations = {
            "vi": {
                "hello": "Xin chào",
                "how are you": "Bạn khỏe không?",
                "good morning": "Chào buổi sáng",
                "good night": "Chúc ngủ ngon",
                "thank you": "Cảm ơn bạn",
                "excuse me": "Xin lỗi",
                "i love you": "Tôi yêu bạn"
            },
            "en": {
                "xin chào": "Hello",
                "bạn khỏe không?": "How are you?",
                "chào buổi sáng": "Good morning",
                "chúc ngủ ngon": "Good night",
                "cảm ơn": "Thank you",
                "xin lỗi": "Excuse me"
            }
        }
        
        translated_text = content
        cleaned_content = content.lower().strip()
        for k, v in translations.get(target_lang, {}).items():
            if k in cleaned_content:
                translated_text = v
                break
                
        if translated_text == content:
            if target_lang == "vi":
                translated_text = f"[Bản dịch tự động]: {content}"
            else:
                translated_text = f"[Translated]: {content}"
                
        await db["messages"].update_one(
            {"_id": message_id},
            {"$set": {"translated_content": translated_text, "translated_lang": target_lang}}
        )
        return {"translated_content": translated_text, "target_lang": target_lang}

    @staticmethod
    async def create_group(group_name: str, member_ids: list, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        import uuid
        from uuid6 import uuid7
        group_id = f"group_{uuid7()}"
        
        all_members = list(set(member_ids + [str(current_user.id)]))
        group = {
            "_id": group_id,
            "group_name": group_name,
            "members": all_members,
            "created_by": str(current_user.id),
            "created_at": datetime.now(timezone.utc)
        }
        await db["chat_groups"].insert_one(group)
        return group

    @staticmethod
    async def save_draft(other_user_id: str, content: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        draft_id = f"draft_{current_user.id}_{other_user_id}"
        await db["chat_drafts"].update_one(
            {"_id": draft_id},
            {
                "$set": {
                    "sender_id": str(current_user.id),
                    "receiver_id": other_user_id,
                    "content": content,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        return {"status": "success", "content": content}

    @staticmethod
    async def get_draft(other_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        draft_id = f"draft_{current_user.id}_{other_user_id}"
        draft = await db["chat_drafts"].find_one({"_id": draft_id})
        if not draft:
            return {"content": ""}
        return {"content": draft.get("content", "")}

    @staticmethod
    async def toggle_self_destruct(other_user_id: str, seconds: int, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        settings_id = f"settings_{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        await db["chat_settings"].update_one(
            {"_id": settings_id},
            {"$set": {"self_destruct_seconds": seconds}},
            upsert=True
        )
        return {"self_destruct_seconds": seconds}

    @staticmethod
    async def toggle_mute(other_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        settings_id = f"settings_{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        settings = await db["chat_settings"].find_one({"_id": settings_id})
        
        muted_by = []
        if settings:
            muted_by = settings.get("muted_by", [])
            
        if str(current_user.id) in muted_by:
            muted_by = [m for m in muted_by if m != str(current_user.id)]
            is_muted = False
        else:
            muted_by.append(str(current_user.id))
            is_muted = True
            
        await db["chat_settings"].update_one(
            {"_id": settings_id},
            {"$set": {"muted_by": muted_by}},
            upsert=True
        )
        return {"is_muted": is_muted}

    @staticmethod
    async def get_conversation_settings(other_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        settings_id = f"settings_{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        settings = await db["chat_settings"].find_one({"_id": settings_id})
        if not settings:
            return {"self_destruct_seconds": 0, "is_muted": False}
            
        muted_by = settings.get("muted_by", [])
        return {
            "self_destruct_seconds": settings.get("self_destruct_seconds", 0),
            "is_muted": str(current_user.id) in muted_by
        }

