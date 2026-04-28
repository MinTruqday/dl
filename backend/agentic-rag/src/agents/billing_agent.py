import httpx
import os
import contextvars
from typing import Annotated, TypedDict, List
from langchain_core.tools import tool, StructuredTool
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langgraph.prebuilt import create_react_agent
from loguru import logger

BACKEND_URL = os.environ.get("CORE_BACKEND_URL")
INTERNAL_API_URL = os.environ.get("INTERNAL_API_URL")

auth_token_var = contextvars.ContextVar("auth_token", default=None)

def get_user_balance(user_id: str) -> str:
    logger.info(f"Balance check requested for user_id: {user_id}")
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để thực hiện thao tác này."

    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.get(f"{INTERNAL_API_URL}/wallet/balance", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            balance = data.get("balance", 0)
            return f"Số dư tài khoản hiện tại: {balance} dl."
        elif response.status_code == 401:
            return "Lỗi xác thực: Phiên đăng nhập đã hết hạn."
        else:
            return f"Lỗi hệ thống: Không thể truy xuất số dư (Mã lỗi: {response.status_code})."
    except Exception as e:
        logger.error(f"Error calling balance API: {e}")
        return "Hệ thống hiện không thể kết nối tới cơ sở dữ liệu."

def get_transaction_history(user_id: str) -> str:
    logger.info(f"Transaction history requested for user_id: {user_id}")
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để xem lịch sử."

    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.get(f"{INTERNAL_API_URL}/wallet/history", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                return "Bạn chưa thực hiện giao dịch nào trong hệ thống."
            
            history_text = ""
            for i, tx in enumerate(data[:5]): 
                tx_type = "Nạp tiền" if tx.get("type") == "TOPUP" else "Thanh toán"
                amount = tx.get("amount", 0)
                note = tx.get("note", "Không có nội dung")
                history_text += f"{i+1}. {tx_type}: {amount} dl - Nội dung: {note}\n"
            return f"Lịch sử 5 giao dịch gần nhất:\n{history_text}"
        else:
            return f"Lỗi hệ thống: Không thể tải lịch sử giao dịch (Mã lỗi: {response.status_code})."
    except Exception as e:
        logger.error(f"Error calling history API: {e}")
        return "Hệ thống gặp sự cố trong quá trình truy vấn dữ liệu giao dịch."

tools = [
    StructuredTool.from_function(
        func=get_user_balance,
        name="get_user_balance",
        description="Tra cứu số dư tài khoản (đơn vị dl) của người dùng."
    ),
    StructuredTool.from_function(
        func=get_transaction_history,
        name="get_transaction_history",
        description="Tra cứu lịch sử giao dịch nạp và tiêu thụ dl của người dùng."
    )
]

llama_model = os.environ.get("LLAMA_MODEL")
hf_token = os.environ.get("HF_TOKEN")

if not llama_model:
    raise ValueError("LLAMA_MODEL environment variable is not set.")

_hf_endpoint = HuggingFaceEndpoint(
    repo_id=llama_model,
    huggingfacehub_api_token=hf_token,
    temperature=0.1
)

llm = ChatHuggingFace(llm=_hf_endpoint)

billing_agent_app = create_react_agent(
    llm,
    tools
)
