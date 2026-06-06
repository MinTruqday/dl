import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timezone, timedelta
import os

async def run():
    client = AsyncIOMotorClient("mongodb://mongodb:27017/")
    db = client.doclib
    
    users = await db.users.find().to_list(length=3)
    
    if len(users) < 2:
        print("Not enough users to create mock chat. Found:", len(users))
        # Create dummy users
        u1_id = "user_" + str(uuid.uuid4())[:8]
        u2_id = "user_" + str(uuid.uuid4())[:8]
        u3_id = "user_" + str(uuid.uuid4())[:8]
        await db.users.insert_many([
            {"_id": u1_id, "username": "mockuser1", "full_name": "Nguyen Van A", "role": "author"},
            {"_id": u2_id, "username": "mockuser2", "full_name": "Tran Thi B", "role": "user"},
            {"_id": u3_id, "username": "mockuser3", "full_name": "Le Van C", "role": "moderator"}
        ])
        users = await db.users.find({"_id": {"$in": [u1_id, u2_id, u3_id]}}).to_list(length=3)
        
    main_user = users[0]
    other_user1 = users[1]
    other_user2 = users[2] if len(users) > 2 else None

    # Clear old mock messages
    await db.messages.delete_many({"sender_id": {"$in": [main_user["_id"], other_user1["_id"]]}})

    messages = [
        {
            "_id": "msg_" + str(uuid.uuid4()),
            "sender_id": other_user1["_id"],
            "receiver_id": main_user["_id"],
            "content": "Chào bạn, mình mới tham gia nền tảng.",
            "is_read": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=1),
            "is_pinned": False,
            "is_edited": False,
            "is_recalled": False,
            "reactions": []
        },
        {
            "_id": "msg_" + str(uuid.uuid4()),
            "sender_id": main_user["_id"],
            "receiver_id": other_user1["_id"],
            "content": "Chào bạn, hoan nghênh bạn nhé. Cần giúp gì cứ hỏi mình.",
            "is_read": True,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=5),
            "is_pinned": False,
            "is_edited": False,
            "is_recalled": False,
            "reactions": []
        },
        {
            "_id": "msg_" + str(uuid.uuid4()),
            "sender_id": other_user1["_id"],
            "receiver_id": main_user["_id"],
            "content": "Bạn cho mình hỏi cách đăng bài như thế nào vậy?",
            "is_read": False,
            "created_at": datetime.now(timezone.utc) - timedelta(minutes=5),
            "is_pinned": False,
            "is_edited": False,
            "is_recalled": False,
            "reactions": []
        }
    ]
    
    if other_user2:
        messages.extend([
            {
                "_id": "msg_" + str(uuid.uuid4()),
                "sender_id": main_user["_id"],
                "receiver_id": other_user2["_id"],
                "content": "Alo admin, mình có gửi báo cáo vi phạm.",
                "is_read": True,
                "created_at": datetime.now(timezone.utc) - timedelta(days=2),
                "is_pinned": False,
                "is_edited": False,
                "is_recalled": False,
                "reactions": []
            },
            {
                "_id": "msg_" + str(uuid.uuid4()),
                "sender_id": other_user2["_id"],
                "receiver_id": main_user["_id"],
                "content": "Mình đã nhận được và đang xử lý nhé.",
                "is_read": False,
                "created_at": datetime.now(timezone.utc) - timedelta(minutes=30),
                "is_pinned": False,
                "is_edited": False,
                "is_recalled": False,
                "reactions": []
            }
        ])

    await db.messages.insert_many(messages)
    print("Mock data inserted successfully!")
    print(f"Main User: {main_user.get('username')} ({main_user.get('_id')})")
    print(f"Other User 1: {other_user1.get('username')} ({other_user1.get('_id')})")
    if other_user2:
        print(f"Other User 2: {other_user2.get('username')} ({other_user2.get('_id')})")

if __name__ == "__main__":
    asyncio.run(run())
