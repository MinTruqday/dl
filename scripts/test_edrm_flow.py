import os
import sys
import uuid
import httpx
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import asyncio

# Setup paths and URLs
DOC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "doc")
DRM_URL = os.getenv("DRM_URL", "http://localhost:8600/drm")

async def test_edrm_flow():
    print("=== Bắt đầu kiểm thử quy trình E-DRM ===")
    
    # 1. Select a file from doc/
    files = [f for f in os.listdir(DOC_DIR) if f.endswith('.pdf')]
    if not files:
        print("Không tìm thấy file PDF nào trong thư mục doc/")
        return
        
    test_file = os.path.join(DOC_DIR, files[0])
    print(f"[1] Chọn file thử nghiệm: {files[0]}")
    
    with open(test_file, 'rb') as f:
        original_pdf_bytes = f.read()
        
    # Mocking Backend Export Flow (In documents service)
    print("\n--- MÔ PHỎNG BACKEND (EXPORT) ---")
    mock_document_id = "test_doc_123"
    mock_user_id = "test_user_456"
    
    print(f"[2] Đăng ký E-DRM với License Server cho User {mock_user_id}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{DRM_URL}/dang-ky",
                json={"document_id": mock_document_id, "user_id": mock_user_id},
                timeout=5.0
            )
            resp.raise_for_status()
            register_data = resp.json()
            
            file_id = register_data["file_id"]
            aes_key_b64 = register_data["aes_key"]
            aes_key = base64.b64decode(aes_key_b64)
            print(f"    -> Đã cấp File ID: {file_id}")
            print(f"    -> Đã cấp Session Key (Base64): {aes_key_b64[:10]}...")
            
    except Exception as e:
        print(f"LỖI: Không thể gọi DRM Server: {e}")
        return

    print("[3] Đang mã hóa file bằng AES-256-GCM...")
    try:
        aesgcm = AESGCM(aes_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, original_pdf_bytes, None)
        
        # Structure: 36 bytes file_id + 12 bytes nonce + ciphertext
        final_doclib_data = file_id.encode('utf-8') + nonce + ciphertext
        print(f"    -> File đã được mã hóa toàn vẹn. Kích thước mới: {len(final_doclib_data)} bytes")
        
        # Save mock file
        output_file = os.path.join(DOC_DIR, f"{files[0]}.doclib")
        with open(output_file, 'wb') as f:
            f.write(final_doclib_data)
        print(f"    -> Đã lưu file mã hóa (.doclib) tại: {output_file}")
    except Exception as e:
        print(f"LỖI: Quá trình mã hóa thất bại: {e}")
        return

    # Mocking Secure Viewer Flow
    print("\n--- MÔ PHỎNG SECURE VIEWER (ĐỌC FILE) ---")
    print(f"[4] Người dùng mở file {files[0]}.doclib...")
    with open(output_file, 'rb') as f:
        encrypted_content = f.read()
        
    extracted_file_id = encrypted_content[:36].decode('utf-8')
    extracted_nonce = encrypted_content[36:48]
    extracted_ciphertext = encrypted_content[48:]
    print(f"    -> Trích xuất File ID: {extracted_file_id}")
    
    print("[5] Trình đọc an toàn yêu cầu khóa giải mã từ DRM Server...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{DRM_URL}/kiem-tra",
                json={"file_id": extracted_file_id},
                timeout=5.0
            )
            resp.raise_for_status()
            acquire_data = resp.json()
            
            acquired_key_b64 = acquire_data["aes_key"]
            acquired_key = base64.b64decode(acquired_key_b64)
            print(f"    -> Đã nhận khóa giải mã: {acquired_key_b64[:10]}...")
    except Exception as e:
        print(f"LỖI: Không thể lấy khóa từ DRM Server: {e}")
        return

    print("[6] Tiến hành giải mã tệp tin trên RAM...")
    try:
        aesgcm = AESGCM(acquired_key)
        decrypted_pdf = aesgcm.decrypt(extracted_nonce, extracted_ciphertext, None)
        
        # Verify it's a PDF
        header = decrypted_pdf[:5].decode('utf-8', errors='ignore')
        if header == "%PDF-":
            print(f"    -> [THÀNH CÔNG] File đã được giải mã chính xác! Kích thước: {len(decrypted_pdf)} bytes")
            print("    -> Cấu trúc PDF nguyên vẹn, sẵn sàng hiển thị (Render) trên Canvas/WASM.")
        else:
            print("    -> [THẤT BẠI] Giải mã thành công nhưng dữ liệu không phải định dạng PDF hợp lệ.")
            
    except Exception as e:
        print(f"LỖI: Trình đọc không thể giải mã tệp (Sai khóa hoặc dữ liệu bị hỏng): {e}")
        return

    print("\n=== QUY TRÌNH E-DRM ĐÃ KIỂM THỬ THÀNH CÔNG ===")

if __name__ == "__main__":
    asyncio.run(test_edrm_flow())
