import asyncio
import httpx
import json

async def test_agentic_ai():
    url = "http://localhost:8008/tro-chuyen/phat-truc-tiep"
    
    payload = {
        "query": "Xin chào, hãy suy nghĩ và cho tôi biết 1 cộng 1 bằng mấy?",
        "useSmart": True,
        "session_id": "test-session",
        "user_id": "01942a03-75bf-73c8-a968-07b4617a26f6",
        "document_ids": []
    }
    
    print("Sending request to Agentic AI (useSmart=True)...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream("POST", url, json=payload) as response:
                print(f"Status: {response.status_code}")
                async for chunk in response.aiter_text():
                    print(chunk, end="")
        except Exception as e:
            print(f"\nRequest failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agentic_ai())
