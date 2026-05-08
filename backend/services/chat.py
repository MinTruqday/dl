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
    async def get_messages(other_user_id: str, current_user: UserInDB, limit: int = 50):
        query = {
            "$or": [
                {"sender_id": current_user.id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": current_user.id}
            ]
        }
        db = db_client.mongodb.get_default_database()
        cursor = db["messages"].find(query).sort("created_at", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        
        for msg in messages:
            if msg.get("reply_to_id"):
                msg["replied_message"] = await db["messages"].find_one({"_id": msg["reply_to_id"]})
        
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
        cursor = db["messages"].aggregate(pipeline)
        conversations = await cursor.to_list(length=100)
        
        results = []
        for conv in conversations:
            other_user = await db["users"].find_one({"_id": conv["_id"]})
            if other_user:
                pinned_cursor = db["messages"].find({
                    "$or": [
                        {"sender_id": current_user.id, "receiver_id": conv["_id"], "is_pinned": True},
                        {"sender_id": conv["_id"], "receiver_id": current_user.id, "is_pinned": True}
                    ]
                }).sort("created_at", -1)
                pinned_messages = await pinned_cursor.to_list(length=5)

                results.append({
                    "other_user_id": conv["_id"],
                    "other_user": {
                        "username": other_user.get("username"),
                        "avatar_url": other_user.get("avatar_url"),
                        "full_name": other_user.get("full_name")
                    },
                    "last_message": conv["last_message"],
                    "pinned_messages": pinned_messages,
                    "unread_count": conv["unread_count"]
                })
        return results
        return results
