from core.database import db_client
from models.chat import MessageInDB, MessageCreate
from models.user import UserInDB
from datetime import datetime
from typing import List

class ChatService:
    @staticmethod
    async def send_message(receiver_id: str, content: str, current_user: UserInDB):
        message = MessageInDB(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content
        )
        await db_client.mongodb["messages"].insert_one(message.model_dump(by_alias=True))
        return message

    @staticmethod
    async def get_messages(other_user_id: str, current_user: UserInDB, limit: int = 50):
        query = {
            "$or": [
                {"sender_id": current_user.id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": current_user.id}
            ]
        }
        cursor = db_client.mongodb["messages"].find(query).sort("created_at", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        
        await db_client.mongodb["messages"].update_many(
            {"sender_id": other_user_id, "receiver_id": current_user.id, "is_read": False},
            {"$set": {"is_read": True}}
        )
        
        return messages[::-1]

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
        
        cursor = db_client.mongodb["messages"].aggregate(pipeline)
        conversations = await cursor.to_list(length=100)
        
        results = []
        for conv in conversations:
            other_user = await db_client.mongodb["users"].find_one({"_id": conv["_id"]})
            if other_user:
                results.append({
                    "other_user_id": conv["_id"],
                    "other_user": {
                        "username": other_user.get("username"),
                        "avatar_url": other_user.get("avatar_url"),
                        "full_name": other_user.get("full_name")
                    },
                    "last_message": conv["last_message"],
                    "unread_count": conv["unread_count"]
                })
        return results
