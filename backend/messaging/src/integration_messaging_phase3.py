import asyncio
import os
import secrets
from datetime import datetime, timezone
import httpx
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run_phase3_tests():
    print("=" * 60)
    print(" BẮT ĐẦU CHẠY THỰC TẾ SMOKE TEST MESSAGING PHASE 3 ")
    print("=" * 60)

    secret = os.getenv("SECRET_KEY", "doclib-secret-key-2026")
    user_id = f"user_{secrets.token_hex(4)}"
    other_user_id = f"user_{secrets.token_hex(4)}"

    token = jwt.encode(
        {
            "sub": "msgphase3@example.com",
            "uid": user_id,
            "sid": "session-msg-p3",
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
    await redis_client.sadd(f"user_sessions:{user_id}", "session-msg-p3")

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://doclib_mongodb:27017")
    mongo = AsyncIOMotorClient(mongo_uri)
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    messaging_db = mongo[os.getenv("MESSAGING_DB_NAME", "doclib_messaging")]

    await humanity_db.users.insert_many([
        {"_id": user_id, "email": f"p3_{secrets.token_hex(3)}@example.com", "full_name": "Tester P3 A", "role": "reader", "is_active": True},
        {"_id": other_user_id, "email": f"p3_{secrets.token_hex(3)}@example.com", "full_name": "Tester P3 B", "role": "reader", "is_active": True},
    ])

    group_id = f"group_{secrets.token_hex(4)}"
    part_key = f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    await messaging_db.conversations.insert_many([
        {"_id": part_key, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
        {"_id": group_id, "name": "Nhóm Thử Nghiệm P3", "creator_id": user_id, "participants": [user_id, other_user_id], "updated_at": datetime.now(timezone.utc)},
    ])

    await messaging_db.message_groups.insert_one({
        "_id": group_id,
        "name": "Nhóm Thử Nghiệm P3",
        "created_by": user_id,
        "members": [user_id, other_user_id],
        "created_at": datetime.now(timezone.utc),
    })

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Test Generate Group Invite Link
            print("\n--- [1] TEST LIVE REST API: TẠO LINK MỜI NHÓM & MÃ QR ---")
            invite_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{group_id}/link-moi",
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{group_id}/link-moi -> Status:", invite_res.status_code)
            print("Response Data:", invite_res.json())
            assert invite_res.status_code == 200
            invite_code = invite_res.json()["data"]["invite_code"]

            # 2. Test Join by Invite Code
            print("\n--- [2] TEST LIVE REST API: GIA NHẬP NHÓM BẰNG LINK/MÃ MỜI ---")
            join_res = await client.post(
                "http://127.0.0.1:8000/tin-nhan/nhom/tham-gia",
                json={"invite_code": invite_code},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/nhom/tham-gia -> Status:", join_res.status_code)
            print("Response Data:", join_res.json())
            assert join_res.status_code == 200

            # 3. Test Set Nickname
            print("\n--- [3] TEST LIVE REST API: ĐẶT BIỆT DANH CUỘC TRÒ CHUYỆN ---")
            nick_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/biet-danh",
                json={"nickname": "Báo Đen"},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/biet-danh -> Status:", nick_res.status_code)
            print("Response Data:", nick_res.json())
            assert nick_res.status_code == 200

            # 4. Test Share Contact Card
            print("\n--- [4] TEST LIVE REST API: CHIA SẺ THẺ DANH THIẾP ---")
            card_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/danh-thiep",
                json={"contact_user_id": other_user_id},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/danh-thiep -> Status:", card_res.status_code)
            print("Response Data:", card_res.json())
            assert card_res.status_code == 200

            # 5. Test Archive Thread
            print("\n--- [5] TEST LIVE REST API: LƯU TRỮ CUỘC TRÒ CHUYỆN ---")
            archive_res = await client.post(
                f"http://127.0.0.1:8000/tin-nhan/{other_user_id}/luu-tru",
                json={"is_archived": True},
                headers={"Authorization": auth_header},
            )
            print("▶ POST /tin-nhan/{other_user_id}/luu-tru -> Status:", archive_res.status_code)
            print("Response Data:", archive_res.json())
            assert archive_res.status_code == 200

        print("\n" + "=" * 60)
        print(" MESSAGING PHASE 3 LIVE REST APIs CHẠY THỰC TẾ & PASS 100% ")
        print("=" * 60)

    finally:
        await humanity_db.users.delete_many({"_id": {"$in": [user_id, other_user_id]}})
        await messaging_db.conversations.delete_many({"_id": {"$in": [part_key, group_id]}})
        await messaging_db.message_groups.delete_one({"_id": group_id})
        await redis_client.delete(f"user_sessions:{user_id}")
        await redis_client.aclose()
        mongo.close()


if __name__ == "__main__":
    asyncio.run(run_phase3_tests())
