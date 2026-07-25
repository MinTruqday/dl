import asyncio
import os
import secrets
from datetime import datetime, timezone
import httpx
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run_phase4_tests():
    print("=" * 60)
    print(" BẮT ĐẦU CHẠY THỰC TẾ SMOKE TEST MESSAGING PHASE 4 ")
    print("=" * 60)

    secret = os.getenv("SECRET_KEY", "doclib-secret-key-2026")
    user_id = f"user_{secrets.token_hex(4)}"
    other_user_id = f"user_{secrets.token_hex(4)}"

    token = jwt.encode(
        {
            "sub": "msgphase4@example.com",
            "uid": user_id,
            "sid": "session-msg-p4",
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
    await redis_client.sadd(f"user_sessions:{user_id}", "session-msg-p4")

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://doclib_mongodb:27017")
    mongo = AsyncIOMotorClient(mongo_uri)
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    messaging_db = mongo[os.getenv("MESSAGING_DB_NAME", "doclib_messaging")]

    await humanity_db.users.insert_many([
        {"_id": user_id, "email": f"p4_{secrets.token_hex(3)}@example.com", "full_name": "Tester P4 A", "role": "reader", "is_active": True},
        {"_id": other_user_id, "email": f"p4_{secrets.token_hex(3)}@example.com", "full_name": "Tester P4 B", "role": "reader", "is_active": True},
    ])

    group_id = f"group_{secrets.token_hex(4)}"
    part_key = f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    await messaging_db.conversations.insert_many([
        {"_id": part_key, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
        {"_id": group_id, "name": "Nhóm Thử Nghiệm P4", "creator_id": user_id, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
    ])

    await messaging_db.message_groups.insert_one({
        "_id": group_id,
        "name": "Nhóm Thử Nghiệm P4",
        "created_by": user_id,
        "members": [user_id, other_user_id],
        "created_at": datetime.now(timezone.utc),
    })

    dummy_msg_id = f"msg_{secrets.token_hex(4)}"
    await messaging_db.messages.insert_one({
        "_id": dummy_msg_id,
        "sender_id": user_id,
        "receiver_id": other_user_id,
        "content": "Nội dung tin nhắn thử nghiệm xuất lịch sử",
        "created_at": datetime.now(timezone.utc),
    })

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Test Hidden Secret Chat PIN Lock
            print("\n--- [1] TEST LIVE REST API: ẨN TRÒ CHUYỆN BẰNG MÃ PIN BẢO MẬT ---")
            pin_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/an-tin-nhan",
                json={"pin_code": "1234"},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/an-tin-nhan -> Status:", pin_res.status_code)
            print("Response Data:", pin_res.json())
            assert pin_res.status_code == 200

            # 2. Test Set Message Alarm
            print("\n--- [2] TEST LIVE REST API: ĐẶT LỊCH NHẮC HẸN TIN NHẮN ---")
            alarm_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{dummy_msg_id}/nhac-hen",
                json={"remind_at": "2026-07-25T08:00:00Z"},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{dummy_msg_id}/nhac-hen -> Status:", alarm_res.status_code)
            print("Response Data:", alarm_res.json())
            assert alarm_res.status_code == 200

            # 3. Test Set Group Slow Mode
            print("\n--- [3] TEST LIVE REST API: CHẾ ĐỘ TIN NHẮN CHẬM CHỐNG SPAM ---")
            slow_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{group_id}/che-do-cham",
                json={"delay_seconds": 10},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{group_id}/che-do-cham -> Status:", slow_res.status_code)
            print("Response Data:", slow_res.json())
            assert slow_res.status_code == 200

            # 4. Test Transfer Group Ownership
            print("\n--- [4] TEST LIVE REST API: CHUYỂN QUYỀN TRƯỞNG NHÓM ---")
            transfer_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{group_id}/chuyen-truong-nhom",
                json={"new_leader_id": other_user_id},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{group_id}/chuyen-truong-nhom -> Status:", transfer_res.status_code)
            print("Response Data:", transfer_res.json())
            assert transfer_res.status_code == 200


            # 5. Test Export Chat History
            print("\n--- [5] TEST LIVE REST API: XUẤT LỊCH SỬ CUỘC TRÒ CHUYỆN (EXPORT) ---")
            export_res = await client.get(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/xuat-lich-su",
                headers={"Authorization": auth_header},
            )
            print("▶ GET /tin-nhan/{other_user_id}/xuat-lich-su -> Status:", export_res.status_code)
            print("Response Data:", export_res.json())
            assert export_res.status_code == 200

        print("\n" + "=" * 60)
        print(" MESSAGING PHASE 4 LIVE REST APIs CHẠY THỰC TẾ & PASS 100% ")
        print("=" * 60)

    finally:
        await humanity_db.users.delete_many({"_id": {"$in": [user_id, other_user_id]}})
        await messaging_db.conversations.delete_many({"_id": {"$in": [part_key, group_id]}})
        await messaging_db.message_groups.delete_one({"_id": group_id})
        await messaging_db.messages.delete_one({"_id": dummy_msg_id})
        await redis_client.delete(f"user_sessions:{user_id}")
        await redis_client.aclose()
        mongo.close()


if __name__ == "__main__":
    asyncio.run(run_phase4_tests())
