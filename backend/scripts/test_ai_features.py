
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_ai_features():
    print("--- STARTING AI FEATURES TEST ---")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login
        print("Step 1: Logging in...")
        login_resp = await client.post(f"{BASE_URL}/xac-thuc/dang-nhap", data={
            "username": "reader@doclib.com",
            "password": "test@123"
        })
        
        if login_resp.status_code != 200:
            print(f"FAILED: Login failed with status {login_resp.status_code}")
            print(login_resp.text)
            return
            
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("SUCCESS: Logged in.")

        # 2. Test Text Processing (AI Service)
        print("\nStep 2: Testing AI Text Processing (/ai/van-ban)...")
        text_resp = await client.post(f"{BASE_URL}/ai/van-ban", json={
            "text": "Xin chào, tôi là một người đọc yêu thích DocLib.",
            "action": "summarize"
        }, headers=headers)
        
        if text_resp.status_code == 200:
            print(f"SUCCESS: Text processing works. Result: {text_resp.json().get('data', '')[:50]}...")
        else:
            print(f"FAILED: Text processing failed with {text_resp.status_code}")
            print(text_resp.text)

        # 3. Test Agentic RAG (Chat)
        print("\nStep 3: Testing Agentic RAG Chat (/ai/truy-van)...")
        chat_resp = await client.post(f"{BASE_URL}/ai/truy-van", json={
            "query": "DocLib là gì?",
            "usePro": False
        }, headers=headers)
        
        if chat_resp.status_code == 200:
            print(f"SUCCESS: RAG Chat works. Answer: {chat_resp.json().get('data', {}).get('answer', '')[:50]}...")
        else:
            print(f"FAILED: RAG Chat failed with {chat_resp.status_code}")
            print(chat_resp.text)

        # 4. Test Semantic Search
        print("\nStep 4: Testing Semantic Search (/ai/tim-kiem)...")
        search_resp = await client.get(f"{BASE_URL}/ai/tim-kiem", params={"q": "sách kinh tế"}, headers=headers)
        
        if search_resp.status_code == 200:
            print(f"SUCCESS: Semantic search works. Results count: {len(search_resp.json().get('data', []))}")
        else:
            print(f"FAILED: Semantic search failed with {search_resp.status_code}")
            print(search_resp.text)

        # 5. Test Inference Routes (e.g., Translate)
        print("\nStep 5: Testing Inference / Translation (/suy-luan/dich-thuat)...")
        trans_resp = await client.post(f"{BASE_URL}/suy-luan/dich-thuat", json={
            "text": "Hello, how are you?",
            "target_lang": "vi"
        }, headers=headers)
        
        if trans_resp.status_code == 200:
            print(f"SUCCESS: Translation works. Result: {trans_resp.json().get('data', '')}")
        else:
            print(f"FAILED: Translation failed with {trans_resp.status_code}")
            print(trans_resp.text)

    print("\n--- AI FEATURES TEST COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(test_ai_features())
