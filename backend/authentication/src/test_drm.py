import asyncio
import jwt
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timezone

import os
SECRET_KEY = "doclib-password"
MONGO_URI = os.environ.get("MONGODB_URI", "mongodb://doclib_mongodb:27017/?authSource=admin")

async def main():
    client = AsyncIOMotorClient(MONGO_URI)
    
    # 1. Tạo User PRO
    pro_uid = str(uuid.uuid4())
    pro_sid = str(uuid.uuid4())
    await client["doclib_humanity"]["users"].insert_one({
        "_id": pro_uid,
        "email": "pro@doclib.com",
        "ai_tier": "PRO"
    })
    
    # 2. Tạo User PREMIUM
    prem_uid = str(uuid.uuid4())
    prem_sid = str(uuid.uuid4())
    await client["doclib_humanity"]["users"].insert_one({
        "_id": prem_uid,
        "email": "premium@doclib.com",
        "ai_tier": "PREMIUM"
    })
    
    # Add session to Redis
    import redis.asyncio as redis
    r = redis.from_url("redis://doclib_redis:6379/0")
    await r.sadd(f"user_sessions:{pro_uid}", pro_sid)
    await r.sadd(f"user_sessions:{prem_uid}", prem_sid)

    # 3. Tạo 2 tài liệu giả
    doc_pro_id = str(uuid.uuid4())
    doc_prem_id = str(uuid.uuid4())
    
    await client["doclib_drm"]["documents"].insert_one({
        "_id": doc_pro_id,
        "title": "Tài liệu PRO",
        "slug": f"tai-lieu-pro-{doc_pro_id}",
        "content": "Nội dung cho gói PRO. Sẽ chỉ có Watermark.",
        "creator_id": pro_uid,
        "is_premium": False
    })
    
    await client["doclib_drm"]["documents"].insert_one({
        "_id": doc_prem_id,
        "title": "Tài liệu PREMIUM",
        "slug": f"tai-lieu-prem-{doc_prem_id}",
        "content": "Nội dung cho gói PREMIUM. Sẽ có E-DRM AESGCM.",
        "creator_id": prem_uid,
        "is_premium": True
    })

    # Tạo tokens
    pro_token = jwt.encode({
        "sub": "pro@doclib.com",
        "sid": pro_sid,
        "uid": pro_uid,
        "role": "reader"
    }, SECRET_KEY, algorithm="HS256")
    
    prem_token = jwt.encode({
        "sub": "premium@doclib.com",
        "sid": prem_sid,
        "uid": prem_uid,
        "role": "reader"
    }, SECRET_KEY, algorithm="HS256")
    
    print("--- Bắt đầu test PRO ---")
    async with httpx.AsyncClient() as http:
        resp = await http.get(f"http://doclib_drm:8013/ket-xuat/{doc_pro_id}/drm", headers={"Authorization": f"Bearer {pro_token}"})
        print(f"Status Code PRO: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type')}")
        print(f"Content-Disposition: {resp.headers.get('content-disposition')}")
        if resp.status_code == 200:
            with open("test_pro_output.pdf", "wb") as f:
                f.write(resp.content)
            print(f"File PDF đã lưu. Size: {len(resp.content)} bytes.")
            # Kiểm tra xem file có phải là PDF hợp lệ không (Bắt đầu bằng %PDF)
            if resp.content.startswith(b"%PDF"):
                print(">> THÀNH CÔNG: Dữ liệu trả về đúng chuẩn PDF.")
            else:
                print(">> THẤT BẠI: Dữ liệu không phải PDF.")

    print("\n--- Bắt đầu test PREMIUM ---")
    async with httpx.AsyncClient() as http:
        resp = await http.get(f"http://doclib_drm:8013/ket-xuat/{doc_prem_id}/drm", headers={"Authorization": f"Bearer {prem_token}"})
        print(f"Status Code PREMIUM: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type')}")
        print(f"Content-Disposition: {resp.headers.get('content-disposition')}")
        if resp.status_code == 200:
            with open("test_premium_output.doclib", "wb") as f:
                f.write(resp.content)
            print(f"File .doclib đã lưu. Size: {len(resp.content)} bytes.")
            # Kiểm tra xem file có bị mã hoá không (không phải PDF)
            if not resp.content.startswith(b"%PDF"):
                print(">> THÀNH CÔNG: Dữ liệu trả về đã được mã hoá AES-GCM (binary .doclib).")
            else:
                print(">> THẤT BẠI: Dữ liệu vẫn là file thô PDF.")
                
    # Dọn dẹp Database
    await client["doclib_humanity"]["users"].delete_one({"_id": pro_uid})
    await client["doclib_humanity"]["users"].delete_one({"_id": prem_uid})
    await client["doclib_content"]["documents"].delete_one({"_id": doc_pro_id})
    await client["doclib_content"]["documents"].delete_one({"_id": doc_prem_id})
    await r.srem(f"user_sessions:{pro_uid}", pro_sid)
    await r.srem(f"user_sessions:{prem_uid}", prem_sid)

if __name__ == "__main__":
    asyncio.run(main())
