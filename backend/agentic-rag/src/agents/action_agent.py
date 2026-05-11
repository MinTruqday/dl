import httpx
import contextvars
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langgraph.prebuilt import create_react_agent
from loguru import logger
from src.core.config import settings

INTERNAL_API_URL = settings.INTERNAL_API_URL
auth_token_var = contextvars.ContextVar("auth_token", default=None)

@tool
async def get_user_balance() -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để thực hiện thao tác này"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{INTERNAL_API_URL}/vi-tien/so-du", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", {})
            balance = data.get("balance", 0)
            return f"Số dư tài khoản hiện tại: {balance} dl"
        elif response.status_code == 401:
            return "Lỗi xác thực: Phiên đăng nhập đã hết hạn"
        return f"Lỗi hệ thống: Không thể truy xuất số dư (Mã lỗi: {response.status_code})"
    except Exception as e:
        logger.error(f"Error calling balance API: {e}")
        return "Hệ thống hiện không thể kết nối tới cơ sở dữ liệu"

@tool
async def get_transaction_history() -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để xem lịch sử"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{INTERNAL_API_URL}/vi-tien/lich-su", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Bạn chưa thực hiện giao dịch nào trong hệ thống"
            history_text = ""
            for i, tx in enumerate(data[:5]): 
                tx_type = "Nạp tiền" if tx.get("type") == "TOPUP" else "Thanh toán"
                amount = tx.get("amount", 0)
                note = tx.get("note", "Không có nội dung")
                history_text += f"{i+1}. {tx_type}: {amount} dl - Nội dung: {note}\n"
            return f"Lịch sử 5 giao dịch gần nhất:\n{history_text}"
        return f"Lỗi hệ thống: Không thể tải lịch sử giao dịch (Mã lỗi: {response.status_code})"
    except Exception as e:
        logger.error(f"Error calling history API: {e}")
        return "Hệ thống gặp sự cố trong quá trình truy vấn dữ liệu giao dịch"

@tool
async def redeem_voucher(code: str) -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để đổi voucher"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INTERNAL_API_URL}/vi-tien/ma-qua-tang/doi-ma", 
                json={"code": code}, 
                headers=headers, 
                timeout=5
            )
        if response.status_code == 200:
            res_data = response.json().get("data", {})
            bonus = res_data.get("bonus_dl", 0)
            return f"Đổi voucher thành công. Tài khoản đã được cộng thêm {bonus} dl"
        data = response.json()
        detail = data.get("detail", "Mã voucher không hợp lệ hoặc đã sử dụng")
        return f"Lỗi đổi voucher: {detail}"
    except Exception as e:
        logger.error(f"Error calling redeem API: {e}")
        return "Hệ thống nạp thẻ hiện đang bảo trì"

@tool
async def get_revenue_report() -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để xem doanh thu"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{INTERNAL_API_URL}/vi-tien/doanh-thu", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", {})
            total = data.get("total_revenue", 0)
            pending = data.get("pending_withdrawal", 0)
            return f"Báo cáo tài chính:\n- Tổng doanh thu: {total} dl\n- Đang chờ thanh toán: {pending} dl"
        return "Không thể truy xuất dữ liệu doanh thu"
    except Exception as e:
        logger.error(f"Error calling revenue API: {e}")
        return "Lỗi kết nối hệ thống tài chính"

@tool
async def send_virtual_tip(target_user_id: str, amount: int) -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để gửi tặng dl"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INTERNAL_API_URL}/vi-tien/tien-ung-ho/{target_user_id}?amount={amount}", 
                headers=headers, 
                timeout=5
            )
        if response.status_code == 200:
            return f"Đã gửi tặng thành công {amount} dl tới người dùng {target_user_id}"
        data = response.json()
        return f"Lỗi giao dịch: {data.get('detail', 'Số dư không đủ hoặc người dùng không tồn tại')}"
    except Exception as e:
        logger.error(f"Error calling tip API: {e}")
        return "Giao dịch thất bại do lỗi hệ thống"

@tool
async def get_my_documents() -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để xem tài liệu"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{INTERNAL_API_URL}/tai-lieu/ca-nhan", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Bạn chưa có tài liệu nào trong thư viện"
            res = "Danh sách tài liệu của bạn:\n"
            for doc in data:
                res += f"- {doc.get('title')} (ID: {doc.get('id')}) - Trạng thái: {doc.get('status')}\n"
            return res
        return "Không thể lấy danh sách tài liệu"
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return "Lỗi kết nối tới thư viện tài liệu"

@tool
async def get_trash_documents() -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{INTERNAL_API_URL}/tai-lieu/thung-rac", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Thùng rác đang trống"
            res = "Tài liệu trong thùng rác:\n"
            for doc in data:
                res += f"- {doc.get('title')} (ID: {doc.get('id')}) - Ngày xóa: {doc.get('deleted_at')}\n"
            return res
        return "Không thể truy cập thùng rác"
    except Exception as e:
        logger.error(f"Error getting trash: {e}")
        return "Lỗi hệ thống khi truy cập thùng rác"

@tool
async def delete_document(document_id: str) -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers, timeout=5)
        if response.status_code == 200:
            return "Đã xóa tài liệu thành công"
        return "Xóa tài liệu thất bại"
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return "Gặp sự cố khi thực hiện lệnh xóa"

@tool
async def restore_document(document_id: str) -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{INTERNAL_API_URL}/tai-lieu/{document_id}/khoi-phuc", headers=headers, timeout=5)
        if response.status_code == 200:
            return "Đã khôi phục tài liệu thành công"
        return "Khôi phục thất bại"
    except Exception as e:
        logger.error(f"Error restoring document: {e}")
        return "Lỗi hệ thống khi khôi phục tài liệu"

@tool
async def get_document_analytics(document_id: str) -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực"
    headers = {"Authorization": token}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{INTERNAL_API_URL}/tai-lieu/{document_id}/phan-tich/roi-rot", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", {})
            dropoff = data.get("dropoff_data", [])
            if not dropoff:
                return "Chưa có dữ liệu thống kê cho tài liệu này"
            res = f"Phân tích độc giả cho tài liệu {document_id}:\n"
            for ch in dropoff:
                res += f"- {ch.get('chapter_title')}: {ch.get('readers_started')} người đọc, tỉ lệ bỏ dở {ch.get('dropoff_rate')}%\n"
            return res
        return "Không thể lấy dữ liệu thống kê"
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return "Lỗi kết nối hệ thống phân tích"

tools = [
    get_user_balance,
    get_transaction_history,
    redeem_voucher,
    get_revenue_report,
    send_virtual_tip,
    get_my_documents,
    get_trash_documents,
    delete_document,
    restore_document,
    get_document_analytics
]

llama_model = settings.LLAMA_MODEL
hf_token = settings.HF_TOKEN

_hf_endpoint = HuggingFaceEndpoint(
    repo_id=llama_model,
    huggingfacehub_api_token=hf_token,
    temperature=0.1
)

llm = ChatHuggingFace(llm=_hf_endpoint)

action_agent_app = create_react_agent(
    llm,
    tools
)
