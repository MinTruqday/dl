import httpx
import contextvars
from typing import List
from langchain_core.tools import StructuredTool
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langgraph.prebuilt import create_react_agent
from loguru import logger
from src.core.config import settings

INTERNAL_API_URL = settings.INTERNAL_API_URL
auth_token_var = contextvars.ContextVar("auth_token", default=None)

def get_user_balance(user_id: str) -> str:
    logger.info(f"get_user_balance requested for user_id: {user_id}")
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để thực hiện thao tác này"

    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.get(f"{INTERNAL_API_URL}/vi-tien/so-du", headers=headers, timeout=5)
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

def get_transaction_history(user_id: str) -> str:
    logger.info(f"get_transaction_history requested for user_id: {user_id}")
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để xem lịch sử"

    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.get(f"{INTERNAL_API_URL}/vi-tien/lich-su", headers=headers, timeout=5)
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

def redeem_voucher(code: str) -> str:
    logger.info(f"Voucher redemption requested")
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để đổi voucher"

    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.post(
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

def get_revenue_report() -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để xem doanh thu"

    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.get(f"{INTERNAL_API_URL}/vi-tien/doanh-thu", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", {})
            total = data.get("total_revenue", 0)
            pending = data.get("pending_withdrawal", 0)
            return f"Báo cáo tài chính:\n- Tổng doanh thu: {total} dl\n- Đang chờ thanh toán: {pending} dl"
        return "Không thể truy xuất dữ liệu doanh thu"
    except Exception as e:
        logger.error(f"Error calling revenue API: {e}")
        return "Lỗi kết nối hệ thống tài chính"

def send_virtual_tip(target_user_id: str, amount: int) -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để gửi tặng dl"

    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.post(
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

tools = [
    StructuredTool.from_function(
        func=get_user_balance,
        name="get_user_balance",
        description="Tra cứu số dư tài khoản (đơn vị dl) của người dùng"
    ),
    StructuredTool.from_function(
        func=get_transaction_history,
        name="get_transaction_history",
        description="Tra cứu lịch sử giao dịch nạp và tiêu thụ dl của người dùng"
    ),
    StructuredTool.from_function(
        func=redeem_voucher,
        name="redeem_voucher",
        description="Đổi voucher để nạp dl vào tài khoản"
    ),
    StructuredTool.from_function(
        func=get_revenue_report,
        name="get_revenue_report",
        description="Xem báo cáo doanh thu và số dl đang chờ thanh toán"
    ),
    StructuredTool.from_function(
        func=send_virtual_tip,
        name="send_virtual_tip",
        description="Gửi tặng dl ủng hộ cho tác giả hoặc người dùng khác"
    )
]

llama_model = settings.LLAMA_MODEL
hf_token = settings.HF_TOKEN

if not llama_model:
    raise ValueError("LLAMA_MODEL environment variable is not set")

_hf_endpoint = HuggingFaceEndpoint(
    repo_id=llama_model,
    huggingfacefacehub_api_token=hf_token,
    temperature=0.1
)

llm = ChatHuggingFace(llm=_hf_endpoint)

billing_agent_app = create_react_agent(
    llm,
    tools
)
