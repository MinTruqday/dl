import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime

async def seed():
    client = AsyncIOMotorClient("mongodb://mongodb:27017")
    db = client["doclib"]
    
    user = await db.users.find_one({"email": "testuser@doclib.com"})
    if not user:
        user_id = str(uuid.uuid4())
        await db.users.insert_one({
            "_id": user_id,
            "email": "testuser@doclib.com",
            "full_name": "Nguyen Van Test",
            "avatar_url": "https://i.pravatar.cc/150?u=testuser",
            "is_active": True,
            "created_at": datetime.utcnow()
        })
        print(f"Created Test User: {user_id}")
    else:
        user_id = user["_id"]
        print(f"Test User already exists: {user_id}")
        
    admin = await db.users.find_one({"email": "admin@doclib.com"})
    if not admin:
        print("Admin user not found, please create admin first.")
        return
    admin_id = admin["_id"]
    
    # Create a 1-on-1 conversation
    conv_key = ":".join(sorted([admin_id, user_id]))
    conv = await db.conversations.find_one({"_id": conv_key})
    if not conv:
        await db.conversations.insert_one({
            "_id": conv_key,
            "type": "direct",
            "participants": [admin_id, user_id],
            "last_message": "Chào bạn, đây là tin nhắn test từ Admin!",
            "last_message_at": datetime.utcnow(),
            "unread_count": {admin_id: 0, user_id: 1},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Insert a message
        msg_id = str(uuid.uuid4())
        await db.messages.insert_one({
            "_id": msg_id,
            "sender_id": admin_id,
            "receiver_id": user_id, # for direct message, receiver_id is the other user
            "content": "Chào bạn, đây là tin nhắn test từ Admin!",
            "is_read": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        print("Đã tạo conversation và tin nhắn mẫu!")
    else:
        print("Conversation đã tồn tại!")
        
    print("Seeding hoàn tất!")

if __name__ == "__main__":
    asyncio.run(seed())
