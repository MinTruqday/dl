from core.database import db_client
from models.chat import MessageInDB, MessageCreate
from models.user import UserInDB
from datetime import datetime, timezone
from typing import List

class ChatService:
    @staticmethod
    async def send_message(receiver_id: str, content: str, current_user: UserInDB, image_url: str = None, reply_to_id: str = None):
        message = MessageInDB(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content,
            image_url=image_url,
            reply_to_id=reply_to_id
        )
        db = db_client.mongodb.get_default_database()
        await db["messages"].insert_one(message.model_dump(by_alias=True))
        res_data = message.model_dump(by_alias=True)
        if reply_to_id:
            res_data["replied_message"] = await db["messages"].find_one({"_id": reply_to_id})
            
        return res_data

    @staticmethod
    async def get_messages(other_user_id: str, current_user: UserInDB, limit: int = 50, cursor: str = None):
        query = {
            "$or": [
                {"sender_id": current_user.id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": current_user.id}
            ]
        }
        
        if cursor:
            from datetime import datetime
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
        if not other_user_ids:
            return []

        users_list = await db["users"].find({"_id": {"$in": other_user_ids}}, {"username": 1, "avatar_url": 1, "full_name": 1}).to_list(length=len(other_user_ids))
        user_map = {str(u["_id"]): u for u in users_list}

        pinned_query = {
            "$or": [],
            "is_pinned": True
        }
        for uid in other_user_ids:
            pinned_query["$or"].append({"sender_id": current_user.id, "receiver_id": uid})
            pinned_query["$or"].append({"sender_id": uid, "receiver_id": current_user.id})
        
        all_pinned = await db["messages"].find(pinned_query).sort("created_at", -1).to_list(length=500)
        pinned_map = {}
        for pm in all_pinned:
            key = pm["receiver_id"] if pm["sender_id"] == current_user.id else pm["sender_id"]
            pinned_map.setdefault(key, [])
            if len(pinned_map[key]) < 5:
                pinned_map[key].append(pm)

        results = []
        for conv in conversations:
            other_user = user_map.get(conv["_id"])
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
        return results

