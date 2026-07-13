import asyncio
import aiohttp
import json

async def main():
    async with aiohttp.ClientSession() as session:
        res = await session.post("http://localhost:8000/lich-su", json={"user_id": "11111111-1111-1111-1111-111111111111", "first_query": "hello world test saving history"})
        data = await res.json()
        session_id = data.get("_id")
        print("Session ID:", session_id)
        
        payload = {
            "query": "hello world test saving history",
            "session_id": session_id,
            "user_id": "11111111-1111-1111-1111-111111111111",
            "thinking": True
        }
        async with session.post("http://localhost:8000/tro-chuyen/phat-truc-tiep", json=payload) as response:
            async for line in response.content:
                print(line.decode().strip())

asyncio.run(main())
