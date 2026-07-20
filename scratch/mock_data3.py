import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def main():
    client = AsyncIOMotorClient("mongodb://mongodb:27017")
    db = client["doclib"]

    # get admin user
    admin = await db["users"].find_one({"email": "admin@doclib.com"})
    if not admin:
        print("No admin user found")
        return

    admin_id = str(admin["_id"])

    # find or create other users
    other_users = []
    for i in range(1, 4):
        email = f"user{i}@doclib.com"
        user = await db["users"].find_one({"email": email})
        if not user:
            user_id = str(uuid.uuid4())
            user = {
                "_id": user_id,
                "email": email,
                "display_name": f"Trần Văn User {i}",
                "slug": f"user-{i}",
                "password_hash": "not_used_for_mock",
                "created_at": datetime.now(timezone.utc)
            }
            await db["users"].insert_one(user)
        other_users.append(str(user["_id"]))

    print(f"Admin: {admin_id}, Others: {other_users}")

    other_user_id = other_users[0]
    
    # Personal Conversation
    existing = await db["conversations"].find_one({
        "participants": {"$all": [admin_id, other_user_id]},
        "_id": {"$not": {"$regex": "^group_"}}
    })
    
    if existing:
        await db["conversations"].update_one(
            {"_id": existing["_id"]},
            {"$set": {"updated_at": datetime.now(timezone.utc)}}
        )
    else:
        await db["conversations"].insert_one({
            "_id": str(uuid.uuid4()),
            "participants": [admin_id, other_user_id],
            "type": "personal",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

    msg1_id = str(uuid.uuid4())
    await db["messages"].insert_one({
        "_id": msg1_id,
        "sender_id": admin_id,
        "receiver_id": other_user_id,
        "content": "Bạn đã xem danh sách đề tài PDF chưa? Đề tài 1 về xây dựng hệ thống RAG khá hay.",
        "created_at": datetime.now(timezone.utc),
        "is_read": True
    })

    msg2_id = str(uuid.uuid4())
    await db["messages"].insert_one({
        "_id": msg2_id,
        "sender_id": other_user_id,
        "receiver_id": admin_id,
        "content": "Mình thấy Giai đoạn 1 yêu cầu thu thập và xử lý tài liệu từ nhiều nguồn khác nhau, có vẻ hơi phức tạp.",
        "created_at": datetime.now(timezone.utc),
        "is_read": True,
        "reply_count": 2
    })

    # Add threaded replies to msg2
    await db["messages"].insert_one({
        "_id": str(uuid.uuid4()),
        "sender_id": admin_id,
        "receiver_id": other_user_id,
        "thread_parent_id": msg2_id,
        "content": "Không sao, mình có thể dùng PyPDF2 hoặc PDFMiner để trích xuất văn bản.",
        "created_at": datetime.now(timezone.utc),
        "is_read": True
    })
    
    await db["messages"].insert_one({
        "_id": str(uuid.uuid4()),
        "sender_id": other_user_id,
        "receiver_id": admin_id,
        "thread_parent_id": msg2_id,
        "content": "Đồng ý, và nếu cần thì dùng thêm OCR nữa.",
        "created_at": datetime.now(timezone.utc),
        "is_read": True
    })

    # Group Conversation
    group_id = "group_" + str(uuid.uuid4())
    members = [admin_id, other_users[0], other_users[1]]
    await db["groups"].insert_one({
        "_id": group_id,
        "name": "Nhóm Thảo luận Đề tài",
        "members": members,
        "created_at": datetime.now(timezone.utc)
    })
    
    await db["conversations"].insert_one({
        "_id": group_id,
        "type": "group",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })

    group_msg1 = str(uuid.uuid4())
    await db["messages"].insert_one({
        "_id": group_msg1,
        "sender_id": admin_id,
        "receiver_id": group_id,
        "content": "Mọi người chọn Đề tài 1 (RAG) hay Đề tài 2 (Chatbot trả lời câu hỏi)?",
        "created_at": datetime.now(timezone.utc),
        "reply_count": 1
    })

    await db["messages"].insert_one({
        "_id": str(uuid.uuid4()),
        "sender_id": other_users[1],
        "receiver_id": group_id,
        "thread_parent_id": group_msg1,
        "content": "Đề tài 2 có Giai đoạn 3 dùng LLM (OpenAI, Anthropic) cũng rất hấp dẫn.",
        "created_at": datetime.now(timezone.utc)
    })

    print("Mock data 3 created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
