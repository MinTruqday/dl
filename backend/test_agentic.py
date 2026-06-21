import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "query": "Tạo một tài liệu ngắn về ngôn ngữ lập trình Python và xuất ra 2 định dạng là Latex và EditorJS",
            "session_id": "test_session_123"
        }
        resp = await client.post("http://localhost:8000/tro-chuyen", json=payload)
        print(f"Status: {resp.status_code}")
        print("Response:")
        print(resp.text)

asyncio.run(main())
