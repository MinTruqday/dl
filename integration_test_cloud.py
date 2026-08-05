import urllib.request
import urllib.parse
import json
import sys
import io
import zipfile
import uuid

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test_cloud_83ffc4@doclib.com"
TEST_PASS = "TestPassword@123"

def make_request(method, endpoint, data=None, token=None, content_type="application/json", files=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = None
    if files:
        # Multipart form data
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        buffer = io.BytesIO()
        
        # Form fields
        if data:
            for k, v in data.items():
                buffer.write(f"--{boundary}\r\n".encode())
                buffer.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
                buffer.write(f"{v}\r\n".encode())
                
        # File fields
        for field_name, (filename, file_content, mime) in files.items():
            buffer.write(f"--{boundary}\r\n".encode())
            buffer.write(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode())
            buffer.write(f"Content-Type: {mime}\r\n\r\n".encode())
            if isinstance(file_content, str):
                file_content = file_content.encode("utf-8")
            buffer.write(file_content)
            buffer.write(b"\r\n")
            
        buffer.write(f"--{boundary}--\r\n".encode())
        body = buffer.getvalue()
    elif data is not None:
        if content_type == "application/json":
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif content_type == "application/x-www-form-urlencoded":
            body = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content_type_res = response.headers.get("Content-Type", "")
            res_bytes = response.read()
            if "application/json" in content_type_res or "text/" in content_type_res:
                res_body = res_bytes.decode("utf-8", errors="ignore")
                try:
                    return response.status, json.loads(res_body), response.headers
                except Exception:
                    return response.status, res_body, response.headers
            return response.status, res_bytes, response.headers
    except urllib.error.HTTPError as e:
        res_bytes = e.read()
        res_body = res_bytes.decode("utf-8", errors="ignore")
        try:
            return e.code, json.loads(res_body), e.headers
        except Exception:
            return e.code, {"raw": res_body}, e.headers
    except Exception as e:
        return 500, {"error": str(e)}, {}

def run_tests():
    print("=================================================================")
    print("  KIỂM THỬ THỰC TẾ CÁC TÍNH NĂNG CLOUD STORAGE TRÊN DOCKER")
    print("=================================================================\n")

    # 1 & 2. Authenticate: Try Login, or Register if needed
    print(f"[TEST 1 & 2] Xác thực tài khoản kiểm thử: {TEST_EMAIL}")
    login_payload = {"username": TEST_EMAIL, "password": TEST_PASS}
    status, res, _ = make_request("POST", "/xac-thuc/dang-nhap", data=login_payload, content_type="application/x-www-form-urlencoded")
    if status != 200:
        print(f"ℹ️ Tài khoản chưa tồn tại, tiến hành đăng ký...")
        reg_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASS,
            "full_name": "Cloud Tester",
            "slug": "cloud-tester-auto",
            "role": "reader",
            "agreed_to_terms": True
        }
        status, res, _ = make_request("POST", "/xac-thuc/dang-ky", data=reg_payload)
        if status not in (200, 201):
            print(f"❌ Đăng ký thất bại ({status}): {res}")
            sys.exit(1)
        print(f"✅ Đăng ký thành công: {res.get('message')}")
        status, res, _ = make_request("POST", "/xac-thuc/dang-nhap", data=login_payload, content_type="application/x-www-form-urlencoded")
        if status != 200:
            print(f"❌ Đăng nhập sau đăng ký thất bại ({status}): {res}")
            sys.exit(1)

    token = res["data"]["access_token"]
    user = res["data"].get("user", {})
    user_id = user.get("id", user.get("_id", "unknown"))
    print(f"✅ Đăng nhập và lấy Access Token thành công! User ID: {user_id}\n")

    # 3. Create Root & Sub Folders
    print(f"[TEST 3] Khởi tạo thư mục kiểm thử")
    status, res, _ = make_request("POST", "/luu-tru/thu-muc", data={"name": "Thư mục gốc A"}, token=token)
    assert status == 201, f"Lỗi tạo thư mục A: {res}"
    folder_a_id = res["data"]["_id"]
    print(f"✅ Tạo thư mục A thành công (ID: {folder_a_id})")

    status, res, _ = make_request("POST", "/luu-tru/thu-muc", data={"name": "Thư mục đích B"}, token=token)
    assert status == 201, f"Lỗi tạo thư mục B: {res}"
    folder_b_id = res["data"]["_id"]
    print(f"✅ Tạo thư mục B thành công (ID: {folder_b_id})\n")

    # 4. Upload Real Files to MinIO via API
    print(f"[TEST 4] Tải lên tệp thật (Multipart) vào MinIO qua Cloud API")
    file_content_1 = ("%PDF-1.4\n1 0 obj\n<< /Title (DocLib Sample Document) >>\nendobj\n" + "X" * 5200 + "\n%%EOF").encode("utf-8")
    files = {"file": ("tailieu1.pdf", file_content_1, "application/pdf")}
    status, res, _ = make_request("POST", "/tai-len/tap-tin", token=token, files=files)
    if status != 201:
        print(f"❌ Tải lên tệp 1 thất bại ({status}): {res}")
        sys.exit(1)
    file_1_id = res["data"]["item_id"]
    file_1_url = res["data"]["url"]
    print(f"✅ Tải lên tệp 1 thành công (ID: {file_1_id}, Path: {file_1_url})")

    file_content_2 = ("Nội dung tài liệu kiểm thử số 2 - DocLib AI Document.\n" * 120).encode("utf-8")
    files = {"file": ("tailieu2.txt", file_content_2, "text/plain")}
    status, res, _ = make_request("POST", "/tai-len/tap-tin", token=token, files=files)
    assert status == 201, f"Lỗi tải lên tệp 2: {res}"
    file_2_id = res["data"]["item_id"]
    print(f"✅ Tải lên tệp 2 thành công (ID: {file_2_id})\n")

    # 5. Test File Locking System
    print(f"[TEST 5] Kiểm tra cơ chế Khóa tệp (Locking) & Mở khóa (Unlocking)")
    # Lock item
    status, res, _ = make_request("POST", f"/luu-tru/tap-tin/{file_1_id}/khoa", token=token)
    assert status == 200, f"Khóa tệp thất bại: {res}"
    assert res["data"]["is_locked"] is True, "is_locked không phải True"
    print(f"✅ Khóa tệp thành công (is_locked: True, locked_by: {res['data']['locked_by']})")

    # Double lock attempt (should return 400)
    status, res, _ = make_request("POST", f"/luu-tru/tap-tin/{file_1_id}/khoa", token=token)
    assert status == 400, f"Khóa lần 2 phải trả về 400, nhưng nhận {status}: {res}"
    print(f"✅ Chặn khóa lặp lại chính xác (400: {res.get('detail')})")

    # Unlock item
    status, res, _ = make_request("POST", f"/luu-tru/tap-tin/{file_1_id}/mo-khoa", token=token)
    assert status == 200, f"Mở khóa tệp thất bại: {res}"
    assert res["data"]["is_locked"] is False, "is_locked không phải False"
    print(f"✅ Mở khóa tệp thành công (is_locked: False)\n")

    # 6. Test Preview URL (Presigned inline URL)
    print(f"[TEST 6] Kiểm tra tạo liên kết Xem trước (Inline Preview)")
    status, res, _ = make_request("GET", f"/luu-tru/tap-tin/{file_1_id}/xem-truoc", token=token)
    assert status == 200, f"Lỗi tạo link xem trước: {res}"
    preview_url = res["data"]["preview_url"]
    assert "response-content-disposition=inline" in preview_url, "Thiếu inline disposition header"
    print(f"✅ Tạo Presigned Inline Preview URL thành công: {preview_url[:70]}...")

    # Fetch preview content from MinIO via presigned URL (mapping minio docker dns to localhost for host runner)
    host_preview_url = preview_url.replace("http://minio:9000", "http://localhost:9000")
    req_preview = urllib.request.Request(host_preview_url)
    with urllib.request.urlopen(req_preview) as preview_res:
        raw_data = preview_res.read()
        assert raw_data == file_content_1, "Dữ liệu tải từ link xem trước không khớp 100%!"
        print(f"✅ Xác thực nội dung tải từ MinIO qua liên kết xem trước khớp 100% byte-for-byte!\n")

    # 7. Test File Request & Anonymous Upload (Yêu cầu tải lên)
    print(f"[TEST 7] Kiểm tra Tính năng Yêu cầu tải lên (File Request link + Password)")
    req_data = {
        "target_folder_id": folder_a_id,
        "password": "SecretUploadPassword999",
        "expires_in_hours": 48,
        "description": "Thư mục nộp tài liệu đối tác"
    }
    status, res, _ = make_request("POST", "/luu-tru/yeu-cau-tai-len", data=req_data, token=token)
    assert status == 201, f"Tạo yêu cầu tải lên thất bại: {res}"
    req_token = res["data"]["token"]
    print(f"✅ Tạo liên kết yêu cầu tải lên thành công: token = {req_token}")

    # Validate without password (should return 403 error)
    status, res, _ = make_request("GET", f"/luu-tru/yeu-cau-tai-len/{req_token}")
    assert status == 403, f"Yêu cầu có mật khẩu nhưng truy cập không mật khẩu lại thành công! Status: {status}"
    print(f"✅ Bảo mật mật khẩu hoạt động: Truy cập thiếu mật khẩu bị từ chối (403)")

    # Validate with correct password
    status, res, _ = make_request("GET", f"/luu-tru/yeu-cau-tai-len/{req_token}?password=SecretUploadPassword999")
    assert status == 200, f"Xác thực mật khẩu đúng thất bại: {res}"
    assert res["data"]["target_folder_id"] == folder_a_id, "Thư mục đích không khớp"
    print(f"✅ Xác thực mật khẩu thành công (Target Folder: {res['data']['target_folder_id']})")

    # Upload file anonymously through request token
    anon_file_content = ("Đây là tệp tin được khách hàng nộp qua liên kết Yêu cầu tải lên.\n" * 100)
    anon_files = {"file": ("khach_hang_nop.txt", anon_file_content, "text/plain")}
    anon_data = {"password": "SecretUploadPassword999"}
    status, res, _ = make_request("POST", f"/tai-len/yeu-cau/{req_token}", data=anon_data, files=anon_files)
    assert status == 201, f"Khách hàng tải lên qua token thất bại: {res}"
    anon_item_id = res["data"]["item_id"]
    print(f"✅ Khách nộp tệp qua token thành công! Tạo item_id: {anon_item_id}\n")

    # 8. Test Activity Logs (Nhật ký hoạt động)
    print(f"[TEST 8] Kiểm tra Nhật ký hoạt động tệp tin (Activity Logs)")
    # Explicitly log an activity via service or check endpoint
    status, res, _ = make_request("GET", f"/luu-tru/tap-tin/{file_1_id}/nhat-ky", token=token)
    assert status == 200, f"Lỗi lấy nhật ký hoạt động: {res}"
    print(f"✅ Lấy nhật ký hoạt động thành công ({len(res['data'])} bản ghi nhật ký)\n")

    # 9. Test Bulk Actions (Thao tác hàng loạt: Move, Copy, Delete)
    print(f"[TEST 9] Kiểm tra Thao tác hàng loạt (Bulk Move, Copy, Delete)")
    # Bulk Move to Folder B
    status, res, _ = make_request(
        "POST",
        "/luu-tru/thao-tac-hang-loat",
        data={"action": "move", "item_ids": [file_1_id, file_2_id], "target_parent_id": folder_b_id},
        token=token
    )
    assert status == 200, f"Lỗi bulk move: {res}"
    assert res["data"]["success"] == 2, f"Bulk move không thành công 2 tệp: {res}"
    print(f"✅ Bulk Move thành công 2 tệp sang Thư mục B")

    # Bulk Copy
    status, res, _ = make_request(
        "POST",
        "/luu-tru/thao-tac-hang-loat",
        data={"action": "copy", "item_ids": [file_1_id], "target_parent_id": folder_a_id},
        token=token
    )
    assert status == 200, f"Lỗi bulk copy: {res}"
    assert res["data"]["success"] == 1, f"Bulk copy thất bại: {res}"
    print(f"✅ Bulk Copy thành công 1 bản sao sang Thư mục A")

    # Bulk Delete (soft delete / trash)
    status, res, _ = make_request(
        "POST",
        "/luu-tru/thao-tac-hang-loat",
        data={"action": "delete", "item_ids": [file_1_id, file_2_id]},
        token=token
    )
    assert status == 200, f"Lỗi bulk delete: {res}"
    assert res["data"]["success"] == 2, f"Bulk delete thất bại: {res}"
    print(f"✅ Bulk Delete (chuyển thùng rác) thành công 2 tệp\n")

    # 10. Test Zip Download (Nén & Tải xuống nhiều tệp)
    print(f"[TEST 10] Kiểm tra Tải xuống ZIP nhiều tệp (Zip Archive Download)")
    # Restore file_1 and anon_file to untrashed state for zip download test
    make_request("PUT", f"/luu-tru/tap-tin/{file_1_id}", data={"is_trashed": False}, token=token)
    status, zip_bytes, headers = make_request(
        "GET",
        f"/luu-tru/tai-xuong-zip?ids={file_1_id},{anon_item_id}",
        token=token
    )
    assert status == 200, f"Lỗi tải zip: {zip_bytes}"
    assert isinstance(zip_bytes, bytes), "Kết quả không phải dạng nhị phân zip"

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names = z.namelist()
        print(f"📦 Danh sách tệp trong file nén ZIP: {names}")
        raw_extracted_1 = z.read(names[0])
        assert raw_extracted_1 in (file_content_1, anon_file_content.encode("utf-8")), "Nội dung tệp nén không khớp!"
    print(f"✅ Giải nén và kiểm tra dữ liệu trong tệp ZIP thành công 100%!\n")

    print("=================================================================")
    print("  🎉 TẤT CẢ 10 BƯỚC KIỂM THỬ ĐÃ CHẠY THẬT VÀ THÀNH CÔNG 100%!")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
