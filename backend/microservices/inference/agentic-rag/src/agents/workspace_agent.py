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
def get_my_documents() -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để xem tài liệu"
    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.get(f"{INTERNAL_API_URL}/tai-lieu/ca-nhan", headers=headers, timeout=5)
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
logger.info("Log message sanitized"))
        return "Lỗi kết nối tới thư viện tài liệu"
def get_trash_documents() -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực"
    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.get(f"{INTERNAL_API_URL}/tai-lieu/thung-rac", headers=headers, timeout=5)
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
logger.info("Log message sanitized"))
        return "Lỗi hệ thống khi truy cập thùng rác"
def delete_document(document_id: str) -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực"
    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.delete(f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers, timeout=5)
        if response.status_code == 200:
            return f"Đã chuyển tài liệu {document_id} vào thùng rác thành công"
        return "Xóa tài liệu thất bại"
    except Exception as e:
logger.info("Log message sanitized"))
        return "Lỗi kết nối khi xóa tài liệu"
def restore_document(document_id: str) -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực"
    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.post(f"{INTERNAL_API_URL}/tai-lieu/{document_id}/khoi-phuc", headers=headers, timeout=5)
        if response.status_code == 200:
            return f"Đã khôi phục tài liệu {document_id} thành công"
        return "Khôi phục tài liệu thất bại"
    except Exception as e:
logger.info("Log message sanitized"))
        return "Lỗi hệ thống khi khôi phục tài liệu"
def get_document_analytics(document_id: str) -> str:
    token = auth_token_var.get()
    if not token:
        return "Lỗi xác thực"
    headers = {"Authorization": token}
    try:
        with httpx.Client() as client:
            response = client.get(f"{INTERNAL_API_URL}/tai-lieu/{document_id}/phan-tich/roi-rot", headers=headers, timeout=5)
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
logger.info("Log message sanitized"))
        return "Lỗi kết nối hệ thống phân tích"
tools = [
    StructuredTool.from_function(
        func=get_my_documents,
        name="get_my_documents",
        description="Lấy danh sách các tài liệu trong thư viện cá nhân của người dùng"
    ),
    StructuredTool.from_function(
        func=get_trash_documents,
        name="get_trash_documents",
        description="Xem danh sách các tài liệu đã bị xóa và nằm trong thùng rác"
    ),
    StructuredTool.from_function(
        func=delete_document,
        name="delete_document",
        description="Xóa một tài liệu (chuyển vào thùng rác) dựa trên ID"
    ),
    StructuredTool.from_function(
        func=restore_document,
        name="restore_document",
        description="Khôi phục một tài liệu từ thùng rác về thư viện chính"
    ),
    StructuredTool.from_function(
        func=get_document_analytics,
        name="get_document_analytics",
        description="Xem báo cáo thống kê độc giả, tỉ lệ đọc hết và tỉ lệ rơi rớt theo từng chương"
    )
]
llama_model = settings.LLAMA_MODEL
hf_token = settings.HF_TOKEN
_hf_endpoint = HuggingFaceEndpoint(
    repo_id=llama_model,
    huggingfacehub_api_token=hf_token,
    temperature=0.1
)
llm = ChatHuggingFace(llm=_hf_endpoint)
workspace_agent_app = create_react_agent(
    llm,
    tools
)
