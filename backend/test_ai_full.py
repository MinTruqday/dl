import asyncio
import httpx
import json

async def main():
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        login_data = {
            "username": "admin",
            "password": "adminpassword"
        }
        resp = await client.post("http://localhost:8000/api/v1/auth/login", data=login_data)
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return
        token = resp.json().get("access_token")
        print("Logged in!")

        
        payload = {
            "query": "Tạo 2 tài liệu mới: một tài liệu tên 'Python Latex' với nội dung là code Latex cơ bản về Python, và một tài liệu tên 'Python EditorJS' với nội dung JSON của EditorJS về Python.",
            "user_id": "admin_id",
            "session_id": "test_session_final",
            "useSmart": True
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("Sending prompt to AI...")
        ai_resp = await client.post("http://localhost:8000/api/v1/ai/tro-chuyen", json=payload, headers=headers)
        print("AI Status:", ai_resp.status_code)
        print("AI Response:", ai_resp.text)

asyncio.run(main())
