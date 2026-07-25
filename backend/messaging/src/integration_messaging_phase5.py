import asyncio
import os
import secrets
from datetime import datetime, timezone
import httpx
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run_phase5_tests():
    print("=" * 60)
    print(" BẮT ĐẦU CHẠY THỰC TẾ SMOKE TEST MESSAGING PHASE 5 ")
    print("=" * 60)

    secret = os.getenv("SECRET_KEY", "doclib-secret-key-2026")
    user_id = f"user_{secrets.token_hex(4)}"
    other_user_id = f"user_{secrets.token_hex(4)}"

    token = jwt.encode(
        {
            "sub": "msgphase5@example.com",
            "uid": user_id,
            "sid": "session-msg-p5",
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
    await redis_client.sadd(f"user_sessions:{user_id}", "session-msg-p5")

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://doclib_mongodb:27017")
    mongo = AsyncIOMotorClient(mongo_uri)
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    messaging_db = mongo[os.getenv("MESSAGING_DB_NAME", "doclib_messaging")]

    await humanity_db.users.insert_many([
        {"_id": user_id, "email": f"p5_{secrets.token_hex(3)}@example.com", "full_name": "Tester P5 A", "role": "reader", "is_active": True},
        {"_id": other_user_id, "email": f"p5_{secrets.token_hex(3)}@example.com", "full_name": "Tester P5 B", "role": "reader", "is_active": True},
    ])

    group_id = f"group_{secrets.token_hex(4)}"
    part_key = f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    await messaging_db.conversations.insert_many([
        {"_id": part_key, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
        {"_id": group_id, "name": "Nhóm Thử Nghiệm P5", "creator_id": user_id, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
    ])

    await messaging_db.message_groups.insert_one({
        "_id": group_id,
        "name": "Nhóm Thử Nghiệm P5",
        "created_by": user_id,
        "members": [user_id, other_user_id],
        "created_at": datetime.now(timezone.utc),
    })

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Test Auto Reply Setup
            print("\n--- [1] TEST LIVE REST API: TIN NHẮN TRẢ LỜI TỰ ĐỘNG KHI VẮNG MẶT ---")
            reply_res = await client.post(
                "http://127.0.0.1:8000/tin-nhan/ca-nhan/tra-loi-tu-dong",
                json={"auto_reply_text": "Tôi hiện đang trong cuộc họp, sẽ phản hồi sớm", "is_enabled": True},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/ca-nhan/tra-loi-tu-dong -> Status:", reply_res.status_code)
            print("Response Data:", reply_res.json())
            assert reply_res.status_code == 200

            # 2. Test Manage Group Messaging Permissions
            print("\n--- [2] TEST LIVE REST API: PHÂN QUYỀN GỬI TIN NHẮN NHÓM ---")
            perm_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{group_id}/quyen-gui-tin-nhan",
                json={"admin_only": True},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{group_id}/quyen-gui-tin-nhan -> Status:", perm_res.status_code)
            print("Response Data:", perm_res.json())
            assert perm_res.status_code == 200

            # 3. Test Create Group Event
            print("\n--- [3] TEST LIVE REST API: SỰ KIỆN ĐẾM NGƯỢC NHÓM ---")
            event_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{group_id}/su-kien",
                json={"title": "Hạn chót nộp báo cáo", "event_time": "2026-07-30T17:00:00Z"},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{group_id}/su-kien -> Status:", event_res.status_code)
            print("Response Data:", event_res.json())
            assert event_res.status_code == 200

            # 4. Test Set VIP Priority Star
            print("\n--- [4] TEST LIVE REST API: ĐÁNH DẤU ƯU TIÊN VIP CUỘC TRÒ CHUYỆN ---")
            vip_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/uu-tien-vip",
                json={"is_vip": True},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/uu-tien-vip -> Status:", vip_res.status_code)
            print("Response Data:", vip_res.json())
            assert vip_res.status_code == 200

        print("\n" + "=" * 60)
        print(" MESSAGING PHASE 5 LIVE REST APIs CHẠY THỰC TẾ & PASS 100% ")
        print("=" * 60)

    finally:
        await humanity_db.users.delete_many({"_id": {"$in": [user_id, other_user_id]}})
        await messaging_db.conversations.delete_many({"_id": {"$in": [part_key, group_id]}})
        await messaging_db.message_groups.delete_one({"_id": group_id})
        await redis_client.delete(f"user_sessions:{user_id}")
        await redis_client.aclose()
        mongo.close()


if __name__ == "__main__":
    asyncio.run(run_phase5_tests())
