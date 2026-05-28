import urllib.request
import json
import time

url = "http://localhost:8100/luong-du-lieu"
payload = json.dumps({
    "query": "Kể cho tôi một câu chuyện 100 chữ",
    "user_id": "test_user_id",
    "useSmart": False
}).encode('utf-8')

headers = {
    "Content-Type": "application/json"
}

start_time = time.time()
print(f"[{start_time}] Bắt đầu gửi request...")

try:
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    with urllib.request.urlopen(req) as response:
        while True:
            line = response.readline()
            if not line:
                break
            decoded_line = line.decode('utf-8').strip()
            if decoded_line:
                timestamp = time.time() - start_time
                print(f"[{timestamp:.2f}s] Nhận line: {decoded_line}")
except Exception as e:
    print(f"Lỗi: {e}")
