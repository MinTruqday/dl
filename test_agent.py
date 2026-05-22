import requests
import json
import sseclient

API_BASE = "http://localhost:8000"

def main():
    print("1. Logging in as admin@doclib.vn...")
    resp = requests.post(f"{API_BASE}/xac-thuc/dang-nhap", data={
        "username": "admin@doclib.vn",
        "password": "Admin@123"
    })
    
    if resp.status_code != 200:
        print("Login failed:", resp.text)
        return
        
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("2. Creating chat session...")
    query = "Nạp 50000 VNĐ vào tài khoản của tôi."
    resp = requests.post(f"{API_BASE}/ai/lich-su", json={"first_query": query}, headers=headers)
    if resp.status_code not in [200, 201]:
        print("Create session failed:", resp.text)
        return
        
    session_id = resp.json()["data"]["_id"]
    print(f"Session ID: {session_id}")
    
    print("3. Sending query to AI...")
    resp = requests.post(
        f"{API_BASE}/ai/tro-chuyen", 
        json={
            "query": query,
            "useSmart": False,
            "session_id": session_id
        }, 
        headers=headers,
        stream=True
    )
    
    client = sseclient.SSEClient(resp)
    
    print("--- AI RESPONSE ---")
    for event in client.events():
        if event.event == "message":
            data = json.loads(event.data)
            print(data.get("chunk", ""), end="", flush=True)
        elif event.event == "status":
            pass
        elif event.event == "tool":
            print(f"\n[Tool used: {json.loads(event.data).get('agent')}]")
        elif event.event == "done":
            break
        elif event.event == "error":
            print("\nError:", event.data)
    print("\n-------------------")
    
if __name__ == "__main__":
    main()
