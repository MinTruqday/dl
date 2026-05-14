import urllib.request
import urllib.parse
import json

data = urllib.parse.urlencode({"username": "admin@doclib.vn", "password": "Admin@123"}).encode()
req = urllib.request.Request("http://localhost:8000/xac-thuc/dang-nhap", data=data)
with urllib.request.urlopen(req) as response:
    login_res = json.loads(response.read())
    token = login_res["data"]["access_token"]
    print("Token:", token[:20] + "...")

req2 = urllib.request.Request("http://localhost:8000/soan-thao/949ee6b3-f46f-4824-959e-076196f4a485/binh-luan")
req2.add_header("Authorization", f"Bearer {token}")
try:
    with urllib.request.urlopen(req2) as response:
        print("Status:", response.status)
        print("Response:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Status:", e.code)
    print("Response:", e.read().decode())
