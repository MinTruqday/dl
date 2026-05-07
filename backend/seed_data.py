import asyncio
import motor.motor_asyncio
import os
from datetime import datetime, timezone
from enum import Enum
import argon2

class RoleEnum(str, Enum):
    READER = "reader"
    AUTHOR = "author"
    MODERATOR = "moderator"
    ADMIN = "admin"

async def seed_all():
    # Use the same DB settings as core
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/doclib")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "doclib")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    
    # Cleanup existing seed data
    collections = ["users", "documents", "status_updates", "transactions", "messages"]
    for coll in collections:
        await db[coll].delete_many({"is_seed": True})
    
    # Hash password using Argon2 to match core security
    password = "Admin@123"
    ph = argon2.PasswordHasher()
    admin_password_hash = ph.hash(password)
    
    # 1. Seed Admin
    admin = {
        "_id": "admin_01",
        "email": "admin@doclib.vn",
        "full_name": "DocLib Administrator",
        "username": "admin",
        "slug": "admin",
        "role": RoleEnum.ADMIN,
        "password_hash": admin_password_hash,
        "is_seed": True,
        "created_at": datetime.now(timezone.utc)
    }
    await db["users"].insert_one(admin)
    
    # 2. Seed author for testing
    author = {
        "_id": "author_1", "email": "a1@doclib.vn", "full_name": "Lê Bình Nam", 
        "username": "binhnam", "slug": "le-binh-nam", "role": RoleEnum.AUTHOR,
        "followers_count": 5000, "is_seed": True, "created_at": datetime.now(timezone.utc)
    }
    await db["users"].insert_one(author)

    # 3. Seed another user
    user2 = {
        "_id": "user_2", "email": "minhtrung@doclib.vn", "full_name": "Cao Minh Trung", 
        "username": "minhtrung", "slug": "cao-minh-trung", "role": RoleEnum.READER,
        "is_seed": True, "created_at": datetime.now(timezone.utc)
    }
    await db["users"].insert_one(user2)

    # 4. Seed Messages for Chat Interface
    messages = [
        {
            "_id": "msg_1",
            "sender_id": "author_1",
            "receiver_id": "admin_01",
            "content": "Chào Admin, tôi muốn hỏi về quy trình duyệt bản thảo mới cho series sắp tới.",
            "is_read": False,
            "is_seed": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "_id": "msg_2",
            "sender_id": "admin_01",
            "receiver_id": "author_1",
            "content": "Chào Nam, quy trình đã được cập nhật trong phần Studio. Bạn có thể kiểm tra hướng dẫn mới nhất nhé.",
            "is_read": True,
            "is_seed": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "_id": "msg_3",
            "sender_id": "author_1",
            "receiver_id": "admin_01",
            "content": "Cảm ơn Admin, tôi đã thấy rồi. Tuyệt vời lắm!",
            "is_read": False,
            "is_seed": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "_id": "msg_4",
            "sender_id": "user_2",
            "receiver_id": "admin_01",
            "content": "Giao diện mới trông rất chuyên nghiệp, đúng chất editorial tôi mong đợi.",
            "is_read": True,
            "is_seed": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "_id": "msg_5",
            "sender_id": "admin_01",
            "receiver_id": "user_2",
            "content": "Cảm ơn Trung đã phản hồi. Chúng tôi vẫn đang tiếp tục hoàn thiện các module còn lại.",
            "is_read": True,
            "is_seed": True,
            "created_at": datetime.now(timezone.utc)
        }
    ]
    await db["messages"].insert_many(messages)

    print("--- SEED COMPLETED: ADMIN, AUTHORS & MESSAGES CREATED SUCCESSFULLY ---")
    print(f"ADMIN LOGIN -> Email: admin@doclib.vn | Password: {password}")

if __name__ == "__main__":
    asyncio.run(seed_all())
