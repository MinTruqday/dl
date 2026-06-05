import httpx
import json
import asyncio
import jwt

prompts = [
    # 1. Giao tiếp cơ bản (Bypass LangGraph)
    "Xin chào, bạn là ai và bạn đóng vai trò gì trong hệ thống DocLib?",
    "Hôm nay thời tiết đẹp quá nhỉ.",
    
    # 2. Tác vụ API Nội bộ - Ví Điện Tử & Giao Dịch
    "Kiểm tra số dư ví dl hiện tại của tôi là bao nhiêu.",
    "Lấy lịch sử giao dịch gần đây nhất của tôi.",
    "Tôi muốn nạp 50000 VNĐ vào tài khoản.",
    
    # 3. Quản lý Tài Liệu Nội Bộ
    "Liệt kê các tài liệu tôi đã tải lên.",
    "Lấy danh sách các tài liệu trong thùng rác.",
    "Tạo một tài liệu mới có tên 'Ghi chú cuộc họp' với nội dung 'Hôm nay họp về dự án AI'.",
    
    # 4. Truy Xuất Tri Thức (RAG / KnowledgeAgent)
    "Hãy tóm tắt ngắn gọn nội dung tài liệu.",
    "Trình bày cấu trúc của tài liệu này.",
    "Khái niệm 'Chunking' trong tài liệu có nghĩa là gì?",
    "So sánh điểm mạnh và yếu của tài liệu này.",
    
    # 5. Phân Tích & Viết Nháp (DraftGenerator / ReasoningAgent)
    "Hãy đóng vai chuyên gia thẩm định và đánh giá tài liệu này.",
    "Đề xuất cho tôi một số trích dẫn từ tài liệu.",
    "Viết một email nháp gửi sếp để báo cáo tiến độ dựa trên tài liệu.",
    "Chuyển đổi văn bản sau sang giọng điệu trang trọng: 'Ê bạn, làm xong cái này chưa?'",
    
    # 6. Viết Code & Toán học (CodeInterpreter)
    "Tính tổng các số từ 1 đến 1000 bằng Python.",
    "Dùng thư viện math tính căn bậc 2 của 123456.",
    "Tạo một biểu đồ ASCII hình sin đơn giản.",
    
    # 7. Tác vụ Đa Bước (Multi-step)
    "Đầu tiên hãy lấy danh sách tài liệu của tôi, sau đó tóm tắt chúng.",
    "Kiểm tra số dư ví của tôi, nếu có đủ tiền thì tạo một voucher.",
    "Đọc tài liệu và sau đó viết một đoạn code Python để đếm số từ trong tài liệu đó."
]

async def run_prompt(p, index):
    print(f"\n--- [{index}/22] RUNNING PROMPT: {p} ---")
    
    token = jwt.encode({"id": "user-123", "role": "admin", "email": "admin@doclib.com"}, "SECRET", algorithm="HS256")
    
    payload = {
        "query": p,
        "session_id": "test_suite_22",
        "user_id": "user-123",
        "useSmart": True,
        "useWeb": False, # disable web to speed up and avoid search limits
        "document_id": "019e92c3-9f02-792a-a307-3ecf552ade16",
        "conversation_history": []
    }
    
    headers = {"Authorization": token}
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", "http://agentic-ai:8100/luong-du-lieu", json=payload, headers=headers, timeout=120) as response:
                result = ""
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line.replace("data: ", "").strip()
                        if data_str == "[DONE]": continue
                        try:
                            data = json.loads(data_str)
                            if "chunk" in data:
                                print(data["chunk"], end="", flush=True)
                                result += data["chunk"]
                        except Exception as e:
                            pass
                print("\n")
                if "Hệ thống đang gặp sự cố" in result or "Lỗi" in result or "Fail" in result:
                    return False
                return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def main():
    print(f"Bắt đầu chạy Test Suite: {len(prompts)} prompts...")
    success_count = 0
    for i, p in enumerate(prompts, 1):
        success = await run_prompt(p, i)
        if success:
            success_count += 1
            
    print(f"\n==========================================")
    print(f"TEST FINISHED: {success_count}/{len(prompts)} SUCCESSFUL")
    print(f"==========================================")

if __name__ == "__main__":
    asyncio.run(main())
