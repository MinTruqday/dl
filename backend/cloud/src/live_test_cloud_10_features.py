import asyncio
import os
import secrets
import json
from datetime import datetime, timezone
import aiohttp
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run_cloud_features_live_test():
    print("=" * 85)
    print("cloud_features_live_test_started")
    print("=" * 85)

    secret = os.environ["SECRET_KEY"]
    user_id = f"user_{secrets.token_hex(4)}"

    token = jwt.encode(
        {
            "sub": "cloud10@example.com",
            "uid": user_id,
            "sid": "session-cloud10",
            "role": "admin",
            "ai_tier": "pro",
            "permissions": [],
            "exp": datetime.now(timezone.utc).timestamp() + 1800,
        },
        secret,
        algorithm="HS256",
    )
    auth_header = f"Bearer {token}"

    redis_uri = os.getenv("REDIS_URI", "redis://doclib_redis:6379")
    redis_client = redis_async.from_url(redis_uri, decode_responses=True)
    await redis_client.sadd(f"user_sessions:{user_id}", "session-cloud10")

    user_profile = {"_id": user_id, "email": "cloud10@example.com", "full_name": "Cloud Tester", "role": "admin"}
    await redis_client.setex(f"profile:{user_id}", 300, json.dumps(user_profile))

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://doclib_mongodb:27017")
    mongo = AsyncIOMotorClient(mongo_uri)
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    cloud_db = mongo[os.getenv("CLOUD_DB_NAME", "doclib_cloud")]

    await humanity_db.users.insert_one({
        "_id": user_id,
        "email": "cloud10@example.com",
        "full_name": "Cloud Tester",
        "role": "admin",
        "storage_limit": 15 * 1024 * 1024 * 1024,
        "is_active": True
    })

    file_id = f"item_{secrets.token_hex(4)}"
    folder_id = f"folder_{secrets.token_hex(4)}"

    await cloud_db.storage_items.insert_many([
        {
            "_id": file_id,
            "name": "Báo cáo doanh thu Q3.pdf",
            "owner_id": user_id,
            "parent_id": None,
            "is_folder": False,
            "size": 5 * 1024 * 1024,
            "mime_type": "application/pdf",
            "url": f"users/{user_id}/bao_cao_q3.pdf",
            "is_trashed": False,
            "is_starred": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "_id": folder_id,
            "name": "Tài liệu dự án 2026",
            "owner_id": user_id,
            "parent_id": None,
            "is_folder": True,
            "size": 0,
            "is_trashed": False,
            "is_starred": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    ])

    passed = 0

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10.0)) as session:
            async with session.post(f"http://127.0.0.1:8000/luu-tru/phien-ban/{file_id}", json={"new_url": f"users/{user_id}/bao_cao_q3_v2.pdf", "new_size": 6000000}, headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_1_passed")

            async with session.get(f"http://127.0.0.1:8000/luu-tru/phien-ban/{file_id}", headers={"Authorization": auth_header}) as res:
                data = await res.json()
                assert res.status in {200, 201} and len(data["data"]) > 0
                passed += 1
                ver_id = data["data"][0]["_id"]
                print("feature_2_passed")

            async with session.post(f"http://127.0.0.1:8000/luu-tru/phien-ban/{file_id}/khoi-phuc/{ver_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_3_passed")

            async with session.delete(f"http://127.0.0.1:8000/luu-tru/thung-rac/chuyen-vao/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_4_passed")

            async with session.post(f"http://127.0.0.1:8000/luu-tru/thung-rac/khoi-phuc/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_5_passed")

            async with session.post("http://127.0.0.1:8000/luu-tru/link-chia-se/tao", json={"item_id": file_id, "password": "SecretPassword123", "expires_in_hours": 48}, headers={"Authorization": auth_header}) as res:
                data = await res.json()
                assert res.status in {200, 201}
                passed += 1
                share_token = data["data"]["share_token"]
                print("feature_6_passed")

            async with session.get(f"http://127.0.0.1:8000/luu-tru/link-chia-se/xac-thuc/{share_token}?password=SecretPassword123") as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_7_passed")

            async with session.post(f"http://127.0.0.1:8000/luu-tru/danh-dau-sao/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_8_passed")

            async with session.get("http://127.0.0.1:8000/luu-tru/danh-dau-sao/danh-sach", headers={"Authorization": auth_header}) as res:
                data = await res.json()
                assert res.status in {200, 201} and len(data["data"]) > 0
                passed += 1
                print("feature_9_passed")

            async with session.get("http://127.0.0.1:8000/luu-tru/dung-luong/phan-tich", headers={"Authorization": auth_header}) as res:
                data = await res.json()
                assert res.status in {200, 201} and "breakdown_bytes" in data["data"]
                passed += 1
                print("feature_10_passed")

            async with session.post(f"http://127.0.0.1:8000/luu-tru/nhan-ban/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_11_passed")

            async with session.get("http://127.0.0.1:8000/luu-tru/tim-kiem-nang-cao?q=Bao+cao&extension=pdf", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_12_passed")

            async with session.post(f"http://127.0.0.1:8000/luu-tru/thu-muc/{folder_id}/mau-sac", json={"color_hex": "#4285F4"}, headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_13_passed")

            async with session.post(f"http://127.0.0.1:8000/luu-tru/phieu-tag/{file_id}", json={"tags": ["Dự án", "Tài chính", "Q3"]}, headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_14_passed")

            async with session.get(f"http://127.0.0.1:8000/luu-tru/xem-truoc/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}
                passed += 1
                print("feature_15_passed")

        print("\n" + "=" * 85)
        print(f"cloud_features_live_test_passed={passed}")
        print("=" * 85)

    finally:
        await humanity_db.users.delete_one({"_id": user_id})
        await cloud_db.storage_items.delete_many({"owner_id": user_id})
        await cloud_db.storage_versions.delete_many({"owner_id": user_id})
        await cloud_db.storage_share_links.delete_many({"owner_id": user_id})
        await redis_client.delete(f"user_sessions:{user_id}")
        await redis_client.delete(f"profile:{user_id}")
        await redis_client.aclose()
        mongo.close()


if __name__ == "__main__":
    asyncio.run(run_cloud_features_live_test())
