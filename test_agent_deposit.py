import httpx
import json
import asyncio

async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Register a dummy user
        print("Registering user...")
        res = await client.post("/xac-thuc/dang-ky", json={
            "email": "testagent2@test.com",
            "password": "Password123!",
            "full_name": "Test Agent 2"
        })
        
        print("Logging in...")
        res = await client.post("/xac-thuc/dang-nhap", data={
            "username": "testagent2@test.com",
            "password": "Password123!"
        })
        
        token = res.json().get("access_token")
        if not token:
            print("Login failed:", res.text)
            return

        print("Testing agent with 'Nạp 50k vào tài khoản'...")
        headers = {"Authorization": f"Bearer {token}"}
        async with client.stream("POST", "/ai/tro-chuyen", json={
            "query": "Tôi muốn nạp 50000 VNĐ vào tài khoản",
            "useSmart": False
        }, headers=headers) as stream:
            async for line in stream.aiter_lines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        js = json.loads(data)
                        if "chunk" in js:
                            print(js["chunk"], end="", flush=True)
                    except:
                        pass
        print("\nTest finished.")

asyncio.run(test())
