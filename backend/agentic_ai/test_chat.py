import asyncio
import httpx
import json

async def main():
    async with httpx.AsyncClient() as client:
        # Create session
        res = await client.post("http://localhost:8000/lich-su", json={"user_id": "test_user_1", "first_query": "hello"})
        session_id = res.json().get("_id")
        print("Session ID:", session_id)
        
        # Stream chat
        payload = {
            "query": "hello",
            "session_id": session_id,
            "user_id": "test_user_1",
            "thinking": False
        }
        async with client.stream("POST", "http://localhost:8000/tro-chuyen/phat-truc-tiep", json=payload, headers={"Accept": "text/event-stream"}) as response:
            async for line in response.aiter_lines():
                if line:
                    print(line)

asyncio.run(main())
