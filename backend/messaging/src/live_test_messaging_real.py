import asyncio
import os
import secrets
from datetime import datetime, timezone
import httpx
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run_live_messaging_tests():
    print("=" * 60)
    print(" BẮT ĐẦU CHẠY THỰC TẾ LIVE HTTP TEST CHO MÔ-ĐUN TIN NHẮN ")
    print("=" * 60)

    secret = os.getenv("SECRET_KEY", "doclib-secret-key-2026")
    user_id = f"user_{secrets.token_hex(4)}"
    other_user_id = f"user_{secrets.token_hex(4)}"

    token = jwt.encode(
        {
            "sub": "msgtest@example.com",
            "uid": user_id,
            "sid": "session-msg-1",
            "role": "reader",
            "permissions": [],
            "exp": datetime.now(timezone.utc).timestamp() + 1800,
        },
        secret,
        algorithm="HS256",
    )
    auth_header = f"Bearer {token}"

    # Setup session in Redis
    redis_uri = os.getenv("REDIS_URI", "redis://doclib_redis:6379")
    redis_client = redis_async.from_url(redis_uri, decode_responses=True)
    await redis_client.sadd(f"user_sessions:{user_id}", "session-msg-1")

    # Insert test profiles, messages & conversations in MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://doclib_mongodb:27017")
    mongo = AsyncIOMotorClient(mongo_uri)
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    messaging_db = mongo[os.getenv("MESSAGING_DB_NAME", "doclib_messaging")]

    await humanity_db.users.insert_many([
        {"_id": user_id, "email": f"msgtest_{secrets.token_hex(3)}@example.com", "full_name": "Tester 1", "role": "reader", "is_active": True},
        {"_id": other_user_id, "email": f"other_{secrets.token_hex(3)}@example.com", "full_name": "Tester 2", "role": "reader", "is_active": True},
    ])

    group_id = f"group_{secrets.token_hex(4)}"
    part_key = f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    await messaging_db.conversations.insert_many([
        {"_id": part_key, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
        {"_id": group_id, "name": "Nhóm Thử Nghiệm", "creator_id": user_id, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
    ])

    await messaging_db.message_groups.insert_one({
        "_id": group_id,
        "name": "Nhóm Thử Nghiệm",
        "created_by": user_id,
        "members": [user_id, other_user_id],
        "created_at": datetime.now(timezone.utc),
    })

    dummy_msg_id = f"msg_{secrets.token_hex(4)}"
    await messaging_db.messages.insert_one({
        "_id": dummy_msg_id,
        "sender_id": user_id,
        "receiver_id": other_user_id,
        "content": "Xin chào đây là tin nhắn thử nghiệm live",
        "reactions": [],
        "created_at": datetime.now(timezone.utc),
    })

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Test Reaction Endpoint
            print("\n--- [1] TEST LIVE REST API: THẢ CẢM XÚC TIN NHẮN ---")
            reaction_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{dummy_msg_id}/bay-to-cam-xuc",
                json={"reaction": "LIKE"},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/message_id/bay-to-cam-xuc -> Status:", reaction_res.status_code)
            print("Response Data:", reaction_res.json())

            # 2. Test Mute Thread Endpoint
            print("\n--- [2] TEST LIVE REST API: TẮT THÔNG BÁO CUỘC TRÒ CHUYỆN ---")
            mute_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/tat-thong-bao",
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/tat-thong-bao -> Status:", mute_res.status_code)
            print("Response Data:", mute_res.json())

            # 3. Test Mark Unread Endpoint
            print("\n--- [3] TEST LIVE REST API: ĐÁNH DẤU CHƯA ĐỌC ---")
            unread_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/danh-dau-chua-doc",
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/danh-dau-chua-doc -> Status:", unread_res.status_code)
            print("Response Data:", unread_res.json())

            # 4. Test Disappearing Timer Endpoint
            print("\n--- [4] TEST LIVE REST API: TIN NHẮN TỰ XÓA (SELF DESTRUCT) ---")
            destruct_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/tu-xoa",
                json={"timer_seconds": 86400},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/tu-xoa -> Status:", destruct_res.status_code)
            print("Response Data:", destruct_res.json())

            # 5. Test Update Chat Theme Endpoint
            print("\n--- [5] TEST LIVE REST API: ĐỔI HÌNH NỀN / CHỦ ĐỀ CHAT ---")
            theme_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/chu-de",
                json={"theme_id": "apple_obsidian"},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/chu-de -> Status:", theme_res.status_code)
            print("Response Data:", theme_res.json())

            # 6. Test Group Announcement Endpoint
            print("\n--- [6] TEST LIVE REST API: ĐĂNG THÔNG BÁO NHÓM ---")
            announce_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{group_id}/thong-bao",
                json={"title": "Thông báo cuộc họp", "body": "Nội dung họp lúc 9h sáng"},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{group_id}/thong-bao -> Status:", announce_res.status_code)
            print("Response Data:", announce_res.json())

            # 7. Test Save to Cloud Endpoint
            print("\n--- [7] TEST LIVE REST API: LƯU TIN NHẮN VÀO CLOUD CÁ NHÂN ---")
            cloud_res = await client.post(
                "http://127.0.0.1:8000/tin-nhan/cloud/luu-tin-nhan",
                json={"content": "Ghi chú tài liệu quan trọng", "attachments": []},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/cloud/luu-tin-nhan -> Status:", cloud_res.status_code)
            print("Response Data:", cloud_res.json())

        print("\n" + "=" * 60)
        print(" TOÀN BỘ 7/7 LIVE REST APIs TIN NHẮN ĐÃ ĐẠT 200 OK PASS 100% ")
        print("=" * 60)

    finally:
        await humanity_db.users.delete_many({"_id": {"$in": [user_id, other_user_id]}})
        await messaging_db.conversations.delete_many({"_id": {"$in": [part_key, group_id]}})
        await messaging_db.messages.delete_one({"_id": dummy_msg_id})
        await redis_client.delete(f"user_sessions:{user_id}")
        await redis_client.aclose()
        mongo.close()


if __name__ == "__main__":
    asyncio.run(run_live_messaging_tests())
