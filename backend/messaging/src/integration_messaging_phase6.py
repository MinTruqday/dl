import asyncio
import os
import secrets
from datetime import datetime, timezone
import httpx
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run_phase6_tests():
    print("=" * 60)
    print(" BẮT ĐẦU CHẠY THỰC TẾ SMOKE TEST MESSAGING PHASE 6 ")
    print("=" * 60)

    secret = os.getenv("SECRET_KEY", "doclib-secret-key-2026")
    user_id = f"user_{secrets.token_hex(4)}"
    other_user_id = f"user_{secrets.token_hex(4)}"

    token = jwt.encode(
        {
            "sub": "msgphase6@example.com",
            "uid": user_id,
            "sid": "session-msg-p6",
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
    await redis_client.sadd(f"user_sessions:{user_id}", "session-msg-p6")

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://doclib_mongodb:27017")
    mongo = AsyncIOMotorClient(mongo_uri)
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    messaging_db = mongo[os.getenv("MESSAGING_DB_NAME", "doclib_messaging")]

    await humanity_db.users.insert_many([
        {"_id": user_id, "email": f"p6_{secrets.token_hex(3)}@example.com", "full_name": "Tester P6 A", "role": "reader", "is_active": True},
        {"_id": other_user_id, "email": f"p6_{secrets.token_hex(3)}@example.com", "full_name": "Tester P6 B", "role": "reader", "is_active": True},
    ])

    group_id = f"group_{secrets.token_hex(4)}"
    part_key = f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    await messaging_db.conversations.insert_many([
        {"_id": part_key, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
        {"_id": group_id, "name": "Nhóm Thử Nghiệm P6", "creator_id": user_id, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
    ])

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Test Auto Clean Schedule
            print("\n--- [1] TEST LIVE REST API: XÓA LỊCH SỬ CHAT ĐỊNH KỲ ---")
            clean_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/xoa-dinh-ky",
                json={"days": 30},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/xoa-dinh-ky -> Status:", clean_res.status_code)
            print("Response Data:", clean_res.json())
            assert clean_res.status_code == 200

            # 2. Test Snooze Notifications
            print("\n--- [2] TEST LIVE REST API: TẮT THÔNG BÁO TẠM THỜI ---")
            snooze_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/tam-tat-thong-bao",
                json={"minutes": 60},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/tam-tat-thong-bao -> Status:", snooze_res.status_code)
            print("Response Data:", snooze_res.json())
            assert snooze_res.status_code == 200

            # 3. Test Get Shared Media Vault
            print("\n--- [3] TEST LIVE REST API: KHO PHƯƠNG TIỆN & TỆP TẬP TRUNG ---")
            vault_res = await client.get(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/kho-phuong-tien",
                headers={"Authorization": auth_header},
            )
            print("▶ GET /tin-nhan/{other_user_id}/kho-phuong-tien -> Status:", vault_res.status_code)
            print("Response Data:", vault_res.json())
            assert vault_res.status_code == 200

            # 4. Test Clear Chat Storage
            print("\n--- [4] TEST LIVE REST API: DỌN DẸP DUNG LƯỢNG LƯU TRỮ ---")
            storage_res = await client.delete(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/don-dung-luong",
                headers={"Authorization": auth_header},
            )
            print("▶ DELETE /tin-nhan/{other_user_id}/don-dung-luong -> Status:", storage_res.status_code)
            print("Response Data:", storage_res.json())
            assert storage_res.status_code == 200

        print("\n" + "=" * 60)
        print(" MESSAGING PHASE 6 LIVE REST APIs CHẠY THỰC TẾ & PASS 100% ")
        print("=" * 60)

    finally:
        await humanity_db.users.delete_many({"_id": {"$in": [user_id, other_user_id]}})
        await messaging_db.conversations.delete_many({"_id": {"$in": [part_key, group_id]}})
        await redis_client.delete(f"user_sessions:{user_id}")
        await redis_client.aclose()
        mongo.close()


if __name__ == "__main__":
    asyncio.run(run_phase6_tests())
