import asyncio
from typing import Optional

import httpx
from loguru import logger

_http_client: Optional[httpx.AsyncClient] = None

def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=httpx.Timeout(30.0),
        )
    return _http_client

async def _make_api_request(method: str, url: str, **kwargs) -> httpx.Response:
    from uuid6 import uuid7

    if method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
        headers = kwargs.get("headers", {})
        if "Idempotency-Key" not in headers:
            headers["Idempotency-Key"] = str(uuid7())
        kwargs["headers"] = headers

    max_retries = 3 if method.upper() == "GET" else 1
    client = _get_client()
    for attempt in range(max_retries):
        try:
            response = await client.request(method, url, **kwargs)
            if response.status_code not in [429, 500, 502, 503, 504]:
                return response
            if attempt == max_retries - 1:
                response.raise_for_status()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
        await asyncio.sleep(2**attempt)
    return response

import jwt

def _check_system_access(token: str) -> bool:
    try:
        from src.core.infrastructure.configuration import settings

        raw_token = token.removeprefix("Bearer ").strip()
        payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=["HS256"])
        role = payload.get("role", "guest")
        return role == "admin"
    except:
        return False

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.prebuilt import create_react_agent
from loguru import logger

from src.core.infrastructure.configuration import settings

INTERNAL_API_URL = settings.INTERNAL_API_URL

@tool
async def get_user_balance(config: RunnableConfig) -> str:
    """Get the current user's DocLib wallet balance in dl currency"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Thao tác này yêu cầu tính bảo mật cao, vui lòng đăng nhập vào tài khoản của bạn và thử lại"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/vi-tien/so-du",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            balance = data.get("balance", 0)
            return f"Số dư tài khoản hiện tại của bạn là {balance} credits"
        elif response.status_code == 401:
            return "Phiên đăng nhập của bạn đã quá hạn an toàn, vui lòng tiến hành đăng nhập lại"
        raise Exception("Lỗi tải số dư tài khoản")
    except Exception as e:
        logger.exception("Lỗi truy cập dữ liệu số dư")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def get_transaction_history(config: RunnableConfig) -> str:
    """View recent financial transaction history including deposit and payments"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Vui lòng xác thực tài khoản để xem chi tiết lịch sử các giao dịch"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/vi-tien/giao-dich",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Chưa ghi nhận bất kỳ giao dịch thanh toán nào trong thời gian gần đây"
            history_text = ""
            for i, tx in enumerate(data[:5]):
                tx_type = "Deposit" if tx.get("type") == "TOPUP" else "Payment"
                amount = tx.get("amount", 0)
                note = tx.get("note", "No content")
                history_text += f"{i+1} {tx_type} transaction of {amount} credits with note {note}\n"
            return f"Dưới đây là lịch sử giao dịch gần đây của bạn\n{history_text}"
        return "Hệ thống đang gặp gián đoạn khi truy xuất lịch sử giao dịch thanh toán của bạn"
    except Exception as e:
        logger.exception("Hệ thống đang gặp gián đoạn khi truy xuất lịch sử giao dịch thanh toán của bạn")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def redeem_voucher(code: str, config: RunnableConfig) -> str:
    """Redeem a gift voucher code to add funds to the account"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Yêu cầu đăng nhập tài khoản hợp lệ để sử dụng mã quà tặng"
    if not code or not code.strip():
        return "Mã khuyến mãi này không hợp lệ hoặc đã được ai đó sử dụng trước đó"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/ma-qua-tang/su-dung",
            json={"code": code.strip()},
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            res_data = response.json().get("data", {})
            bonus = res_data.get("bonus_dl", 0)
            return f"Đổi mã quà tặng thành công và tài khoản của bạn đã được cộng {bonus} credits"
        return "Hệ thống không thể xử lý yêu cầu quy đổi mã quà tặng lúc này"
    except Exception as e:
        logger.exception("Lỗi xử lý yêu cầu đổi thưởng")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def get_revenue_report(config: RunnableConfig) -> str:
    """View revenue report from document sales, intended for authors"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Để bảo mật, vui lòng đăng nhập tài khoản trước khi xem báo cáo doanh thu"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/rut-tien/doanh-thu",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            total = data.get("total_revenue", 0)
            pending = data.get("pending_withdrawal", 0)
            return f"Báo cáo tài chính cho thấy tổng doanh thu là {total} currency units with {pending} units pending withdrawal"
        return "Không thể truy xuất số liệu thống kê doanh thu tài chính"
    except Exception as e:
        logger.exception("Lỗi tải báo cáo doanh thu")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def get_my_documents(config: RunnableConfig) -> str:
    """List all personal documents owned or published by the current user"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Vui lòng đăng nhập vào hệ thống để có thể duyệt thư viện tài liệu của bạn"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/ca-nhan",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Hiện tại thư viện cá nhân của bạn chưa có bất kỳ tài liệu nào"
            res = "Here is the list of your available documents\n"
            for doc in data:
                res += f"Document {doc.get('title')} is currently in {doc.get('status')} status\n"
            return res
        return "Gặp khó khăn trong việc tải danh sách tài liệu từ cơ sở dữ liệu"
    except Exception as e:
        logger.exception("Gặp khó khăn trong việc tải danh sách tài liệu từ MongoDB")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def get_trash_documents(config: RunnableConfig) -> str:
    """View deleted documents currently in the trash bin"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Bạn cần phải xác thực danh tính để tiếp tục"
    if not _check_system_access(token):
        return "Cảnh báo bảo mật: Bạn không có đủ đặc quyền để can thiệp vào khu vực này"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/thung-rac",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Không có tài liệu nào đang nằm trong khu vực thùng rác của bạn"
            res = "The following documents are located within the trash bin\n"
            for doc in data:
                res += f"Document {doc.get('title')} was deleted on {doc.get('deleted_at')}\n"
            return res
        return "Đường truyền truy cập vào dữ liệu thùng rác đang gặp sự cố"
    except Exception as e:
        logger.exception("Lỗi tải danh sách mục đã xóa")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def delete_document(document_id: str, config: RunnableConfig) -> str:
    """Delete a document by ID, moving it to the trash bin"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống yêu cầu bạn đăng nhập để xác nhận quyền sở hữu trước khi xóa tài liệu"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "DELETE",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            try:
                from src.store.database import vector_store

                await vector_store.delete_by_document(document_id)
                logger.info("Dọn dẹp chỉ mục tài liệu thành công")
            except Exception as e:
                logger.exception("Lỗi dọn dẹp chỉ mục tài liệu")
            return "Tài liệu đã được dọn dẹp và xóa bỏ hoàn toàn khỏi hệ thống"
        return "Thao tác xóa bỏ tài liệu đã thất bại do lỗi hệ thống"
    except Exception as e:
        logger.exception("Thao tác xóa bỏ tài liệu đã thất bại do lỗi hệ thống")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def restore_document(document_id: str, config: RunnableConfig) -> str:
    """Restore a document from the trash bin by its ID"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Bạn cần phải xác thực danh tính để tiếp tục"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/khoi-phuc",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            return "Tài liệu của bạn đã được khôi phục thành công về trạng thái ban đầu"
        return "Quá trình khôi phục tài liệu từ thùng rác đã thất bại"
    except Exception as e:
        logger.exception("Quá trình khôi phục tài liệu từ thùng rác đã thất bại")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def get_document_analytics(document_id: str, config: RunnableConfig) -> str:
    """View detailed analytics including read count and drop-off rate for a document"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Bạn cần phải xác thực danh tính để tiếp tục"
    if not _check_system_access(token):
        return "Bạn không được cấp đủ đặc quyền để thực thi thao tác này"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/phan-tich/bo-do",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            readers = data.get("readers_started", 0)
            rate = data.get("dropoff_rate", 0)
            return f"Phân tích độc giả cho thấy {readers} readers with a bounce rate of {rate} percent"
        return "Gặp lỗi trong việc tổng hợp và xuất dữ liệu báo cáo thống kê"
    except Exception as e:
        logger.exception("Lỗi truy xuất dữ liệu phân tích")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

async def _get_doc_text(document_id: str, token: str) -> str:
    try:
        res = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers={"Authorization": token},
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if res.status_code == 200:
            return res.json().get("data", {}).get("content", "")
    except Exception as e:
        logger.exception("Lỗi tải nội dung tài liệu")
    return ""

from src.api.inference import peer_review, suggest_citations, transform_tone

from src.schemas.inference import CitationRequest, ReviewRequest, ToneRequest

@tool
async def agent_suggest_citations(document_id: str, config: RunnableConfig) -> str:
    """Suggest academic citations for a document by its ID"""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Phần nội dung thực tế của tài liệu hiện không khả dụng"
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.DEFAULT_CHUNK_SIZE * 2, chunk_overlap=0
    )
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = CitationRequest(text=safe_text, style="APA")
        data = await suggest_citations(req)
        return f"Dưới đây là các trích dẫn đề xuất cho tài liệu\n\n{data.get('citations', '')}"
    except Exception as e:
        logger.exception("Lỗi tạo gợi ý trích dẫn")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def agent_peer_review(document_id: str, config: RunnableConfig) -> str:
    """Perform a peer review of a document, evaluating strengths and weaknesses"""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Phần nội dung thực tế của tài liệu hiện không khả dụng"
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.DEFAULT_CHUNK_SIZE * 4, chunk_overlap=0
    )
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ReviewRequest(text=safe_text)
        data = await peer_review(req)
        return f"Dưới đây là báo cáo phản biện cho tài liệu\n\n{data.get('review_report', '')}"
    except Exception as e:
        logger.exception("Lỗi quá trình đánh giá chéo")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def agent_transform_tone(
    document_id: str, tone: str, config: RunnableConfig
) -> str:
    """Transform the writing tone of a document, e.g. academic, professional, casual"""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Phần nội dung thực tế của tài liệu hiện không khả dụng"
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.DEFAULT_CHUNK_SIZE * 2, chunk_overlap=0
    )
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ToneRequest(text=safe_text, tone=tone, expansion=False)
        data = await transform_tone(req)
        return f"Dưới đây là văn bản đã được chuyển đổi theo văn phong yêu cầu\n\n{data.get('transformed_text', '')}"
    except Exception as e:
        logger.exception("Lỗi thay đổi giọng văn")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def create_deposit_link(amount: int, config: RunnableConfig) -> str:
    """Create a deposit link to top up the dl wallet. Amount is in VND. Returns a payment URL"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Bạn cần phải xác thực tài khoản trước khi tiến hành nạp tiền"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/nap-tien",
            json={"amount": amount},
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code in [200, 201]:
            data = response.json().get("data", {})
            checkout_url = data.get("checkout_url") or data.get("payment_url")
            if checkout_url:
                return f"Yêu cầu nạp {amount} currency units has been created please visit the following link to proceed with the payment [Pay here]({checkout_url}/)"
            return "Hệ thống không thể khởi tạo đường dẫn thanh toán an toàn tại thời điểm này"
        return "Gặp lỗi nghiêm trọng khi bắt đầu tiến trình giao dịch thanh toán"
    except Exception as e:
        logger.exception("Lỗi xử lý yêu cầu nạp tiền")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

from src.workflow.reduction import agent_summarize_long_document

@tool
async def create_document(
    title: str, description: str, content: str, format: str, config: RunnableConfig
) -> str:
    """Create a new document.
    format: must be 'json' (for Standard Editor) or 'latex' (for LaTeX Editor).
    title: The title of the document.
    description: A short summary.
    content: The main body of the document.
             For 'latex', this MUST be a full valid LaTeX document (including \\documentclass, \\usepackage, etc.).
             For 'json', this MUST be a valid JSON string representing EditorJS data, containing a 'blocks' array. Example: {"blocks": [{"type": "header", "data": {"text": "Title", "level": 2}}, {"type": "paragraph", "data": {"text": "Hello"}}]}
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Bạn cần phải xác thực danh tính để tiếp tục"

    headers = {"Authorization": token}

    import datetime
    import re
    import unicodedata

    slug = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^\w\s-]", "", slug).strip().lower()
    slug = re.sub(r"[-\s]+", "-", slug)

    user_name = "User"
    try:
        res_profile = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/ho-so/ca-nhan",
            headers=headers,
            timeout=settings.DEFAULT_HTTP_TIMEOUT,
        )
        if res_profile.status_code == 200:
            profile_data = res_profile.json().get("data", {})
            user_name = (
                profile_data.get("full_name") or profile_data.get("name") or "User"
            )
    except Exception as e:
        logger.exception("Lỗi tải hồ sơ người dùng để lấy thông tin tác giả")

    if format == "latex":
        if "\\documentclass" not in content:
            month_year = datetime.datetime.now().strftime("%B %Y")
            content = f"\\documentclass[12pt,a4paper]{{article}}\n\\usepackage{{graphicx}}\n\\usepackage{{amsmath}}\n\\title{{{title}}}\n\\author{{{user_name}}}\n\\date{{{month_year}}}\n\\begin{{document}}\n\\maketitle\n\n{content}\n\\end{{document}}"
    elif format == "json":
        import json

        try:
            parsed = json.loads(content)
            if "blocks" not in parsed:
                parsed["blocks"] = [{"type": "paragraph", "data": {"text": content}}]
            parsed["time"] = int(datetime.datetime.now().timestamp() * 1000)
            if "version" not in parsed:
                parsed["version"] = "2.29.1"
            content = json.dumps(parsed)
        except:
            blocks = []
            for paragraph in content.split("\n\n"):
                if paragraph.strip():
                    blocks.append(
                        {"type": "paragraph", "data": {"text": paragraph.strip()}}
                    )
            content = json.dumps(
                {
                    "time": int(datetime.datetime.now().timestamp() * 1000),
                    "blocks": blocks,
                    "version": "2.29.1",
                }
            )

    try:
        create_payload = {
            "title": title,
            "slug": f"{slug}-{int(datetime.datetime.now().timestamp())}",
            "description": description,
            "visibility": "private",
            "content_format": format,
            "content": content,
            "status": "draft",
        }
        res_create = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/tai-lieu/",
            headers=headers,
            json=create_payload,
        )
        if res_create.status_code in [200, 201]:
            new_doc = res_create.json().get("data", {})
            doc_id = new_doc.get("id") or new_doc.get("_id")
            if doc_id:
                return f"Tạo tài liệu mới thành công [Xem tài liệu](/editor?document_id={doc_id})"
            return "Tài liệu đã được khởi tạo thành công trên hệ thống nhưng không thể truy xuất mã định danh"
        return "Quá trình khởi tạo và lưu trữ tài liệu mới đã gặp trục trặc"
    except Exception as e:
        raise Exception(f"Đã xảy ra một lỗi bất thường trong quá trình xử lý luồng dữ liệu: {e}")

@tool
async def read_document(document_id: str, config: RunnableConfig) -> str:
    """Read the content of a document by its ID. Use this before updating a document so you know its current content"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Bạn cần phải xác thực danh tính để tiếp tục"

    headers = {"Authorization": token}
    try:
        res = await _make_api_request(
            "GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers
        )
        if res.status_code != 200:
            return "Không thể trích xuất dữ liệu thông tin chi tiết của tài liệu"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Lỗi tải tài liệu: {e}")

    format = doc_data.get("content_format", "json")
    content = doc_data.get("content", "")

    if format == "json":
        return f"Tài liệu sử dụng định dạng tiêu chuẩn với nội dung sau\n{content}"
    elif format == "latex":
        return f"Tài liệu sử dụng định dạng toán học với nội dung sau\n{content}"
    else:
        return f"Tài liệu sử dụng định dạng thay thế với nội dung sau\n{content}"

@tool
async def update_document(
    document_id: str,
    new_content: str = None,
    title: str = None,
    description: str = None,
    config: RunnableConfig = None,
) -> str:
    """Update an existing document's content, title, or description by its ID. Only provide the fields you want to update.
    - If format is 'json', new_content MUST be a valid EditorJS JSON string (with "blocks" array).
    - If format is 'latex', new_content MUST be the full LaTeX source code.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Bạn cần phải xác thực danh tính để tiếp tục"

    headers = {"Authorization": token}

    try:
        res = await _make_api_request(
            "GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers
        )
        if res.status_code != 200:
            return "Thao tác không được phép: Do hạn chế về quyền bảo mật hoặc tài liệu không còn tồn tại"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Lỗi tải tài liệu: {e}")

    payload = {}
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description

    if new_content:
        format = doc_data.get("content_format", "json")
        if format == "json":
            import datetime
            import json

            try:
                parsed = json.loads(new_content)
                if "blocks" not in parsed:
                    parsed["blocks"] = [
                        {"type": "paragraph", "data": {"text": new_content}}
                    ]
                parsed["time"] = int(datetime.datetime.now().timestamp() * 1000)
                final_content = json.dumps(parsed)
            except:
                blocks = []
                for p in new_content.split("\n\n"):
                    if p.strip():
                        blocks.append(
                            {"type": "paragraph", "data": {"text": p.strip()}}
                        )
                final_content = json.dumps(
                    {
                        "time": int(datetime.datetime.now().timestamp() * 1000),
                        "blocks": blocks,
                        "version": "2.29.1",
                    }
                )
        elif format == "latex":
            final_content = new_content
        else:
            final_content = new_content
        payload["content"] = final_content

    if not payload:
        return "Không có bất kỳ sự thay đổi nội dung nào được ghi nhận trên tài liệu này"

    try:
        res_update = await _make_api_request(
            "PUT",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers=headers,
            json=payload,
        )
        if res_update.status_code in [200, 201]:
            return f"Cập nhật tài liệu thành công [Xem tài liệu](/editor?document_id={document_id})"
        raise Exception("Lỗi cập nhật tài liệu")
    except Exception as e:
        raise Exception(f"Đã xảy ra một lỗi bất thường trong quá trình xử lý luồng dữ liệu: {e}")

@tool
async def translate_document(
    document_id: str, target_language: str, config: RunnableConfig
) -> str:
    """Translate an existing document to a target language. If language is not specified, default to English. Creates a new translated document"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Bạn cần phải xác thực danh tính để tiếp tục"

    headers = {"Authorization": token}

    try:
        res = await _make_api_request(
            "GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers
        )
        if res.status_code != 200:
            return "Không thể trích xuất dữ liệu thông tin chi tiết của tài liệu"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Lỗi tải tài liệu: {e}")

    original_content = doc_data.get("content", "")
    format = doc_data.get("content_format", "json")
    original_title = doc_data.get("title", "Document")

    if not original_content:
        return "Tài liệu này hoàn toàn trống hoặc không chứa nội dung văn bản hợp lệ để thực hiện dịch thuật"

    import json

    text_to_translate = ""
    if format == "json":
        try:
            parsed = json.loads(original_content)
            blocks = parsed.get("blocks", [])
            texts = []
            for b in blocks:
                text_content = b.get("data", {}).get("text", "")
                if text_content:
                    texts.append(text_content)
            text_to_translate = "\n\n".join(texts)
        except:
            text_to_translate = str(original_content)
    else:
        text_to_translate = original_content

    try:
        payload = {"text": text_to_translate, "target_lang": target_language}
        trans_res = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/suy-luan/dich-thuat",
            headers=headers,
            json=payload,
            timeout=60,
        )
        if trans_res.status_code != 200:
            return "Dịch vụ thông dịch ngôn ngữ hiện đang gặp sự cố kết nối"
        translated_text = trans_res.json().get("translation", "")
    except Exception:
        return "Toàn bộ chu trình dịch thuật tài liệu đã bị hủy do phát sinh lỗi"

    if not translated_text:
        return "Quá trình thông dịch nội dung tài liệu đã gặp lỗi không xác định"

    import datetime

    new_title = f"[Translation {target_language}] {original_title}"

    if format == "json":
        new_blocks = []
        for p in translated_text.split("\n\n"):
            if p.strip():
                new_blocks.append({"type": "paragraph", "data": {"text": p.strip()}})
        new_blocks.append(
            {
                "type": "paragraph",
                "data": {"text": "<i>Content generated by DocLib AI</i>"},
            }
        )
        new_content = json.dumps(
            {
                "time": int(datetime.datetime.now().timestamp() * 1000),
                "blocks": new_blocks,
                "version": "2.29.1",
            }
        )
    elif format == "latex":
        if "\\end{document}" in translated_text:
            new_content = translated_text.replace(
                "\\end{document}",
                "\\vspace{1em}\n\\noindent\\textit{Content generated by DocLib AI}\n\\end{document}",
            )
        else:
            new_content = (
                translated_text
                + "\n\n\\vspace{1em}\n\\noindent\\textit{Content generated by DocLib AI}"
            )
    else:
        new_content = translated_text + "\n\n(Content generated by DocLib AI)"

    try:
        import datetime
        import re
        import unicodedata

        slug = (
            unicodedata.normalize("NFKD", new_title)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        slug = re.sub(r"[^\w\s-]", "", slug).strip().lower()
        slug = re.sub(r"[-\s]+", "-", slug)

        create_payload = {
            "title": new_title,
            "slug": f"{slug}-{int(datetime.datetime.now().timestamp())}",
            "description": f"Translation to {target_language} of document {original_title}",
            "visibility": "private",
            "content_format": format,
            "content": new_content,
            "status": "draft",
        }
        res_create = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/tai-lieu/",
            headers=headers,
            json=create_payload,
        )
        if res_create.status_code in [200, 201]:
            new_doc = res_create.json().get("data", {})
            new_doc_id = new_doc.get("id") or new_doc.get("_id")
            if new_doc_id:
                return f"Tạo và lưu bản dịch thành công, bạn có thể xem tại đây [Xem bản dịch](/editor?document_id={new_doc_id})"
            return "Bản dịch đã hoàn tất nhưng không thể liên kết với mã định danh tệp tin"
        return "Quá trình dịch thuật đã hoàn tất nhưng gặp sự cố khi lưu trữ kết quả vào máy chủ"
    except Exception as e:
        logger.exception("Lỗi trong quá trình tạo tài liệu dịch")
        raise Exception(f"Một sự cố bất khả kháng đã xảy ra, mong bạn thông cảm và thao tác lại: {e}")

@tool
async def inspect_ui_components(query: str, config: RunnableConfig) -> str:
    """Dynamically search and read custom EditorJS blocks from the project's source code.
    Use this to understand the required JSON schema for specific components (e.g., query='Chart', 'Kanban', 'Mermaid').
    """
    import os
    import glob
    try:
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
        frontend_dir = os.path.join(workspace_root, "frontend/features/editor/components")

        results = []
        for file_path in glob.glob(f"{frontend_dir}/*{query}*.ts*", recursive=True):
            basename = os.path.basename(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                results.append(f"--- Component: {basename} ---\n{content[:2000]}")

        if not results:
            return f"No custom UI components found matching '{query}'. Try a different keyword."
        return "\n\n".join(results)
    except Exception as e:
        return f"Không thể khởi tạo và xuất tệp tài liệu dịch thuật mới: {e}"

tools = [
    agent_summarize_long_document,
    get_user_balance,
    get_transaction_history,
    redeem_voucher,
    get_revenue_report,
    get_my_documents,
    read_document,
    get_trash_documents,
    delete_document,
    restore_document,
    get_document_analytics,
    agent_suggest_citations,
    agent_peer_review,
    agent_transform_tone,
    create_document,
    update_document,
    create_deposit_link,
    translate_document,
    inspect_ui_components,
]

llama_model = settings.LLAMA_MODEL
hf_token = settings.HF_TOKEN

_hf_endpoint = HuggingFaceEndpoint(
    task="conversational",
    repo_id=llama_model,
    huggingfacehub_api_token=hf_token,
    temperature=0.1,
)

llm = ChatHuggingFace(llm=_hf_endpoint)
