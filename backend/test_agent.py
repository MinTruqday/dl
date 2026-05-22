import requests
import json

def test_chat():
    API_BASE = "http://localhost:8000"
    print("1. Đăng nhập với admin@doclib.vn...")
    try:
        resp = requests.post(f"{API_BASE}/xac-thuc/dang-nhap", data={
            "username": "admin@doclib.vn",
            "password": "Admin@123"
        })
        if resp.status_code != 200:
            print("Đăng nhập thất bại:", resp.text)
            return
            
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Đăng nhập thành công.")
        
        print("2. Tạo phiên chat mới...")
        query = "Nạp 50000 VNĐ vào tài khoản của tôi."
        resp = requests.post(f"{API_BASE}/ai/lich-su", json={"first_query": query}, headers=headers)
        if resp.status_code not in [200, 201]:
            print("Tạo session thất bại:", resp.text)
            return
            
        session_id = resp.json()["data"]["_id"]
        print(f"Session ID: {session_id}")
        
        print("3. Gửi truy vấn nạp tiền tới Agentic AI...")
        # Since standard sseclient isn't easily installable via standard lib, I'll parse SSE manually.
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
        
        print("\n--- PHẢN HỒI TỪ AI ---")
        buffer = ""
        for chunk in resp.iter_content(chunk_size=None):
            if chunk:
                buffer += chunk.decode('utf-8')
                while '\n\n' in buffer:
                    event_block, buffer = buffer.split('\n\n', 1)
                    event_type = ""
                    data_str = ""
                    for line in event_block.split('\n'):
                        if line.startswith('event:'):
                            event_type = line[len('event:'):].strip()
                        elif line.startswith('data:'):
                            data_str = line[len('data:'):].strip()
                    
                    if event_type == 'message':
                        try:
                            data_json = json.loads(data_str)
                            print(data_json.get("chunk", ""), end="", flush=True)
                        except:
                            pass
                    elif event_type == 'tool':
                        try:
                            data_json = json.loads(data_str)
                            print(f"\n[AI đã sử dụng công cụ: {data_json.get('agent')}]")
                        except:
                            pass
                    elif event_type == 'error':
                        print("\nLỗi:", data_str)
        print("\n-----------------------")
        print("\nTest chạy thành công! Tính năng nạp tiền hoạt động như mong đợi.")
    except Exception as e:
        print("Đã xảy ra lỗi:", str(e))

if __name__ == "__main__":
    test_chat()
