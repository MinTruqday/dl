import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _make_api_request(method: str, url: str, **kwargs) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, **kwargs)
        if response.status_code in [429, 500, 502, 503, 504]:
            response.raise_for_status()
        return response


import jwt
def _check_admin(token: str) -> bool:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        role = payload.get("role", "student")
        return role in ["admin", "teacher"]
    except:
        return False

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langgraph.prebuilt import create_react_agent
from loguru import logger
from src.core.config import settings

INTERNAL_API_URL = settings.INTERNAL_API_URL

@tool
async def get_user_balance(config: RunnableConfig) -> str:
    """Get the current user's DocLib wallet balance in dl currency."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để thực hiện thao tác này"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/vi-tien/so-du", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json().get("data", {})
            balance = data.get("balance", 0)
            return f"Số dư tài khoản hiện tại: {balance} dl"
        elif response.status_code == 401:
            return "Lỗi xác thực: Phiên đăng nhập đã hết hạn"
        return f"Lỗi hệ thống: Không thể truy xuất số dư (Mã lỗi: {response.status_code})"
    except Exception as e:
        logger.error(f"Error calling balance API: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def get_transaction_history(config: RunnableConfig) -> str:
    """View recent financial transaction history including deposits and payments."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để xem lịch sử"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/vi-tien/lich-su", headers=headers, timeout=30)
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
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def redeem_voucher(code: str, config: RunnableConfig) -> str:
    """Redeem a gift voucher code to add funds to the account."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để đổi voucher"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request("POST", 
                f"{INTERNAL_API_URL}/vi-tien/ma-qua-tang/doi-ma", 
                json={"code": code}, 
                headers=headers, 
                timeout=30
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
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def get_revenue_report(config: RunnableConfig) -> str:
    """View revenue report from document sales, intended for authors."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để xem doanh thu"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/vi-tien/doanh-thu", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json().get("data", {})
            total = data.get("total_revenue", 0)
            pending = data.get("pending_withdrawal", 0)
            return f"Báo cáo tài chính:\n- Tổng doanh thu: {total} dl\n- Đang chờ thanh toán: {pending} dl"
        return "Không thể truy xuất dữ liệu doanh thu"
    except Exception as e:
        logger.error(f"Error calling revenue API: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def send_virtual_tip(target_user_id: str, amount: int, config: RunnableConfig) -> str:
    """Send a virtual tip in dl currency to another user or author."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để gửi tặng dl"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request("POST", 
                f"{INTERNAL_API_URL}/vi-tien/tien-ung-ho/{target_user_id}?amount={amount}", 
                headers=headers, 
                timeout=30
            )
        if response.status_code == 200:
            return f"Đã gửi tặng thành công {amount} dl tới người dùng {target_user_id}"
        data = response.json()
        return f"Lỗi giao dịch: {data.get('detail', 'Số dư không đủ hoặc người dùng không tồn tại')}"
    except Exception as e:
        logger.error(f"Error calling tip API: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def get_my_documents(config: RunnableConfig) -> str:
    """List all personal documents owned or published by the current user."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để xem tài liệu"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/ca-nhan", headers=headers, timeout=30)
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
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def get_trash_documents(config: RunnableConfig) -> str:
    """View deleted documents currently in the trash bin."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực"
    if not _check_admin(token):
        return "UnauthorizedException: Bạn không có quyền khôi phục tài liệu này."

    headers = {"Authorization": token}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/thung-rac", headers=headers, timeout=30)
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
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def delete_document(document_id: str, config: RunnableConfig) -> str:
    """Delete a document by ID, moving it to the trash bin."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập"
    if not _check_admin(token):
        return "UnauthorizedException: Bạn không có quyền xóa tài liệu này."

    headers = {"Authorization": token}
    try:
        import langchain
        try:
            if langchain.llm_cache:
                langchain.llm_cache.clear()
                logger.info("Cleared Semantic Cache due to document update")
        except Exception as e:
            pass
        response = await _make_api_request("DELETE", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers, timeout=30)
        if response.status_code == 200:
            return "Đã xóa tài liệu thành công"
        return "Xóa tài liệu thất bại"
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def restore_document(document_id: str, config: RunnableConfig) -> str:
    """Restore a document from the trash bin by its ID."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực"
    if not _check_admin(token):
        return "UnauthorizedException: Bạn không có quyền khôi phục tài liệu này."

    headers = {"Authorization": token}
    try:
        import langchain
        try:
            if langchain.llm_cache:
                langchain.llm_cache.clear()
                logger.info("Cleared Semantic Cache due to document update")
        except Exception as e:
            pass
        response = await _make_api_request("POST", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/khoi-phuc", headers=headers, timeout=30)
        if response.status_code == 200:
            return "Đã khôi phục tài liệu thành công"
        return "Khôi phục thất bại"
    except Exception as e:
        logger.error(f"Error restoring document: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def create_document(title: str, content: str, config: RunnableConfig) -> str:
    """Create a new document with the provided title and content."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập"
    if not _check_admin(token):
        return "UnauthorizedException: Bạn không có quyền xóa tài liệu này."

    headers = {"Authorization": token}
    
    import re
    import unicodedata
    slug = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    
    payload = {
        "title": title,
        "slug": slug,
        "content": content,
        "content_format": "html"
    }
    try:
        response = await _make_api_request("POST", f"{INTERNAL_API_URL}/tai-lieu/", json=payload, headers=headers, timeout=30)
        if response.status_code == 201:
            data = response.json().get("data", {})
            return f"Đã tạo tài liệu/bài đăng thành công! ID tài liệu: {data.get('_id', data.get('id'))}"
        return f"Tạo tài liệu thất bại: {response.text}"
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def get_document_analytics(document_id: str, config: RunnableConfig) -> str:
    """View detailed analytics including read count and drop-off rate for a document."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực"
    if not _check_admin(token):
        return "UnauthorizedException: Bạn không có quyền khôi phục tài liệu này."

    headers = {"Authorization": token}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/phan-tich/roi-rot", headers=headers, timeout=30)
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
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

async def _get_doc_text(document_id: str, token: str) -> str:
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers={"Authorization": f"Bearer {token}"}, timeout=30)
        if res.status_code == 200:
            return res.json().get("data", {}).get("content", "")
    except Exception as e:
        logger.error(f"Error fetching doc: {e}")
    return ""

from src.api.inference import generate_mindmap, suggest_citations, peer_review, transform_tone
from src.schemas.inference import MindmapRequest, CitationRequest, ReviewRequest, ToneRequest

@tool
async def agent_generate_mindmap(document_id: str, config: RunnableConfig) -> str:
    """Generate a mindmap structure for a document by its ID."""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text: return "Không tìm thấy nội dung tài liệu."
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = MindmapRequest(text=safe_text, depth=2)
        data = await generate_mindmap(req)
        import json
        return f"Đã tạo cấu trúc bản đồ tư duy thành công:\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
    except Exception as e:
        logger.error(f"Error in mindmap: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def agent_suggest_citations(document_id: str, config: RunnableConfig) -> str:
    """Suggest academic citations for a document by its ID."""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text: return "Không tìm thấy nội dung tài liệu."
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = CitationRequest(text=safe_text, style="APA")
        data = await suggest_citations(req)
        return f"Gợi ý trích dẫn:\n\n{data.get('citations', '')}"
    except Exception as e:
        logger.error(f"Error in citations: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def agent_peer_review(document_id: str, config: RunnableConfig) -> str:
    """Perform a peer review of a document, evaluating strengths and weaknesses."""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text: return "Không tìm thấy nội dung tài liệu."
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ReviewRequest(text=safe_text, criteria=["logic", "rõ ràng"])
        data = await peer_review(req)
        return f"Báo cáo thẩm định:\n\n{data.get('review_report', '')}"
    except Exception as e:
        logger.error(f"Error in peer review: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

@tool
async def agent_transform_tone(document_id: str, tone: str, config: RunnableConfig) -> str:
    """Transform the writing tone of a document, e.g. academic, professional, casual."""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text: return "Không tìm thấy nội dung tài liệu."
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ToneRequest(text=safe_text, tone=tone, expansion=False)
        data = await transform_tone(req)
        return f"Văn bản đã biến đổi ({tone}):\n\n{data.get('transformed_text', '')}"
    except Exception as e:
        logger.error(f"Error transforming tone: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."


@tool
async def create_deposit_link(amount: int, config: RunnableConfig) -> str:
    """Create a deposit link to top up the dl wallet. Amount is in VND. Returns a payment URL."""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Vui lòng đăng nhập để nạp tiền"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request("POST", 
                f"{INTERNAL_API_URL}/nap-tien/tao-link", 
                json={"amount": amount}, 
                headers=headers, 
                timeout=30
            )
        if response.status_code in [200, 201]:
            data = response.json().get("data", {})
            checkout_url = data.get("checkout_url") or data.get("payment_url")
            if checkout_url:
                return f"Đã tạo yêu cầu nạp {amount} VNĐ thành công. Vui lòng truy cập đường dẫn sau để thanh toán: [Thanh toán tại đây]({checkout_url})"
            return "Không thể lấy đường dẫn thanh toán từ hệ thống"
        return "Lỗi khởi tạo thanh toán"
    except Exception as e:
        logger.error(f"Error calling deposit API: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."




from src.workflow.map_reduce import agent_summarize_long_document

tools = [
    agent_summarize_long_document,
    get_user_balance,
    get_transaction_history,
    redeem_voucher,
    get_revenue_report,
    send_virtual_tip,
    get_my_documents,
    get_trash_documents,
    delete_document,
    restore_document,
    get_document_analytics,
    agent_generate_mindmap,
    agent_suggest_citations,
    agent_peer_review,
    agent_transform_tone,
    create_document,
    create_deposit_link
]

llama_model = settings.LLAMA_MODEL
hf_token = settings.HF_TOKEN

_hf_endpoint = HuggingFaceEndpoint(
    repo_id=llama_model,
    huggingfacehub_api_token=hf_token,
    temperature=0.1
)

llm = ChatHuggingFace(llm=_hf_endpoint)
