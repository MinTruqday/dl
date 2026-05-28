import requests
import json
import time

def test_all_ai_features():
    API_BASE = "http://localhost:8000"
    print("1. Đăng nhập với admin@doclib.com...")
    try:
        resp = requests.post(f"{API_BASE}/xac-thuc/dang-nhap", data={
            "username": "admin@doclib.com",
            "password": "123456"
        })
        if resp.status_code != 200:
            print("Đăng nhập thất bại:", resp.text)
            return
            
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        print("Đăng nhập thành công.")
        
        tests = [
            {
                "name": "Xử lý văn bản",
                "method": "POST",
                "url": f"{API_BASE}/ai/van-ban",
                "payload": {"text": "Xin chào", "action": "translate", "target_lang": "en"}
            },
            {
                "name": "Tìm kiếm thông minh",
                "method": "GET",
                "url": f"{API_BASE}/ai/tim-kiem-thong-minh?q=test",
                "payload": None
            },
            {
                "name": "Tạo bản đồ tư duy",
                "method": "POST",
                "url": f"{API_BASE}/ai/tao-ban-do-tu-duy",
                "payload": {"text": "Trí tuệ nhân tạo là gì?", "depth": 2}
            },
            {
                "name": "Biến đổi văn bản",
                "method": "POST",
                "url": f"{API_BASE}/ai/bien-doi-van-ban",
                "payload": {"text": "Hello world", "tone": "professional", "expansion": False}
            },
            {
                "name": "Gợi ý trích dẫn",
                "method": "POST",
                "url": f"{API_BASE}/ai/trich-dan-thong-minh",
                "payload": {"text": "Einstein phát minh ra thuyết tương đối.", "style": "APA"}
            }
        ]

        for i, test in enumerate(tests, 2):
            print(f"\n{i}. Kiểm tra: {test['name']}...")
            try:
                if test["method"] == "POST":
                    r = requests.post(test["url"], json=test["payload"], headers=headers)
                else:
                    r = requests.get(test["url"], headers=headers)
                
                print(f"Status: {r.status_code}")
                if r.status_code == 200:
                    print("=> Thành công.")
                else:
                    print(f"=> Thất bại: {r.text}")
            except Exception as e:
                print(f"=> Lỗi kết nối: {e}")
            time.sleep(1) # Sleep to avoid rate limits

        # Test streaming chat
        print(f"\n{len(tests) + 2}. Kiểm tra Chat Streaming...")
        r_session = requests.post(f"{API_BASE}/ai/lich-su", json={"first_query": "Hello"}, headers=headers)
        if r_session.status_code in [200, 201]:
            session_id = r_session.json()["data"]["_id"]
            r_chat = requests.post(
                f"{API_BASE}/ai/tro-chuyen", 
                json={"query": "Hello", "useSmart": False, "session_id": session_id}, 
                headers=headers,
                stream=True
            )
            print(f"Chat status: {r_chat.status_code}")
            if r_chat.status_code == 200:
                print("=> Stream bắt đầu...")
                for chunk in r_chat.iter_lines():
                    if chunk:
                        print(chunk.decode('utf-8'))
                        break # Just read the first chunk to verify stream works
            else:
                print(f"=> Chat thất bại: {r_chat.text}")
        else:
            print(f"=> Tạo session thất bại: {r_session.text}")

        print("\nHoàn tất bộ kiểm tra!")
    except Exception as e:
        print("Lỗi hệ thống trong quá trình test:", str(e))

if __name__ == "__main__":
    test_all_ai_features()
