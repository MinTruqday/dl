import asyncio
import os
import secrets
import json
from datetime import datetime, timezone
import aiohttp
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run_10_cloud_features_live_test():
    print("=" * 85)
    print(" BẮT ĐẦU TEST TOÀN BỘ 10 TÍNH NĂNG CLOUD THEO TIÊU CHUẨN GOOGLE DRIVE / GOOGLE CLOUD ")
    print("=" * 85)

    secret = os.getenv("SECRET_KEY", "doclib-secret-key-2026")
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
            # 1. Tạo phiên bản mới của tệp tin
            async with session.post(f"http://127.0.0.1:8000/luu-tru/phien-ban/{file_id}", json={"new_url": f"users/{user_id}/bao_cao_q3_v2.pdf", "new_size": 6000000}, headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [1/10] Tạo phiên bản tệp tin mới (Versioning): PASS 201 Created")

            # 2. Lấy lịch sử phiên bản tệp tin
            async with session.get(f"http://127.0.0.1:8000/luu-tru/phien-ban/{file_id}", headers={"Authorization": auth_header}) as res:
                data = await res.json()
                assert res.status in {200, 201} and len(data["data"]) > 0; passed += 1
                ver_id = data["data"][0]["_id"]
                print(f"▶ [2/10] Trích xuất lịch sử phiên bản tệp tin: PASS 200 OK")

            # 3. Khôi phục phiên bản tệp tin cũ
            async with session.post(f"http://127.0.0.1:8000/luu-tru/phien-ban/{file_id}/khoi-phuc/{ver_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [3/10] Khôi phục phiên bản tệp tin chỉ định: PASS 200 OK")

            # 4. Đưa tệp tin vào Thùng rác & Khôi phục
            async with session.delete(f"http://127.0.0.1:8000/luu-tru/thung-rac/chuyen-vao/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [4/10] Chuyển tệp tin vào Thùng rác (Trash Bin): PASS 200 OK")

            async with session.post(f"http://127.0.0.1:8000/luu-tru/thung-rac/khoi-phuc/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [5/10] Khôi phục tệp tin từ Thùng rác: PASS 200 OK")

            # 5. Tạo link chia sẻ công khai bảo vệ bằng mật khẩu
            async with session.post("http://127.0.0.1:8000/luu-tru/link-chia-se/tao", json={"item_id": file_id, "password": "SecretPassword123", "expires_in_hours": 48}, headers={"Authorization": auth_header}) as res:
                data = await res.json()
                assert res.status in {200, 201}; passed += 1
                share_token = data["data"]["share_token"]
                print(f"▶ [6/10] Tạo link chia sẻ bảo vệ mật khẩu & Hạn dùng: PASS 201 Created")

            async with session.get(f"http://127.0.0.1:8000/luu-tru/link-chia-se/xac-thuc/{share_token}?password=SecretPassword123") as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [7/10] Xác thực mật khẩu đường dẫn chia sẻ thành công: PASS 200 OK")

            # 6. Đánh dấu sao tệp nổi bật (Starred Files)
            async with session.post(f"http://127.0.0.1:8000/luu-tru/danh-dau-sao/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [8/10] Đánh dấu sao tệp nổi bật (Starred): PASS 200 OK")

            async with session.get("http://127.0.0.1:8000/luu-tru/danh-dau-sao/danh-sach", headers={"Authorization": auth_header}) as res:
                data = await res.json()
                assert res.status in {200, 201} and len(data["data"]) > 0; passed += 1
                print(f"▶ [9/10] Trích xuất danh sách tệp nổi bật: PASS 200 OK")

            # 7. Phân tích dung lượng theo phân loại (Category Quota Analytics)
            async with session.get("http://127.0.0.1:8000/luu-tru/dung-luong/phan-tich", headers={"Authorization": auth_header}) as res:
                data = await res.json()
                assert res.status in {200, 201} and "breakdown_bytes" in data["data"]; passed += 1
                print(f"▶ [10/10] Phân tích dung lượng theo loại tệp (Quota Analytics): PASS 200 OK")

            # 8. Nhân bản tệp tin (Make a Copy)
            async with session.post(f"http://127.0.0.1:8000/luu-tru/nhan-ban/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [11/10] Nhân bản tệp tin (Make a Copy): PASS 201 Created")

            # 9. Tìm kiếm tệp tin nâng cao (Advanced Search)
            async with session.get("http://127.0.0.1:8000/luu-tru/tim-kiem-nang-cao?q=Bao+cao&extension=pdf", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [12/10] Tìm kiếm tệp nâng cao theo định dạng & từ khóa: PASS 200 OK")

            # 10. Đổi màu thư mục & Đánh thẻ Tag AI
            async with session.post(f"http://127.0.0.1:8000/luu-tru/thu-muc/{folder_id}/mau-sac", json={"color_hex": "#4285F4"}, headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [13/10] Đổi màu sắc thư mục Hex: PASS 200 OK")

            async with session.post(f"http://127.0.0.1:8000/luu-tru/phieu-tag/{file_id}", json={"tags": ["Dự án", "Tài chính", "Q3"]}, headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [14/10] Đánh thẻ nhãn Tag phân loại tệp: PASS 200 OK")

            # 11. Xem trước tệp đa năng (Universal Previewer)
            async with session.get(f"http://127.0.0.1:8000/luu-tru/xem-truoc/{file_id}", headers={"Authorization": auth_header}) as res:
                assert res.status in {200, 201}; passed += 1
                print(f"▶ [15/10] Trình xem trước tệp đa năng (Universal Previewer): PASS 200 OK")

        print("\n" + "=" * 85)
        print(f" CHÚC MỪNG: TOÀN BỘ 10 TÍNH NĂNG PRIVATE CLOUD CHUẨN GOOGLE DRIVE ĐÃ PASS 100% ")
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
    asyncio.run(run_10_cloud_features_live_test())
