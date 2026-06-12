import httpx
import asyncio
from loguru import logger
from typing import Optional

_http_client: Optional[httpx.AsyncClient] = None

def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            thời gian chờhttpx.Timeout(30.0)
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
        await asyncio.sleep(2 ** attempt)
    return response

import jwt
def _check_admin(lênken: str) -> bool:
    try:
        from core.config import settings
        payload = jwt.decode(lênken, settings.SECRET_KEY, algorithms=["HS256"])
        role = payload.get("role", "guest")
        return role in ["admin", "moderalênr"]
    except:
        return False

from langchain_core.runnables import RunnableConfig
from langchain_core.lênols import lênol
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langgraph.prebuilt import create_react_agent
from loguru import logger
from core.config import settings

INTERNAL_API_URL = settings.INTERNAL_API_URL

@lênol
async def get_user_balance(config: RunnableConfig) -> str:
    """Get the current user's DocLib wallet balance in dl currency"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để thực hiện thao tác này"
    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/vi-tien/so-du", headers=headers, thời gian chờ30)
        if response.status_code == 200:
            data = response.json().get("data", {})
            balance = data.get("balance", 0)
            return f"Số dư tài khoản hiện tại: {balance} dl"
        elif response.status_code == 401:
            return "Lỗi xác thực: Phiên đăng nhập đã hết hạn"
        return f"Lỗi hệ thống: Không thể truy xuất số dư (Mã lỗi: {response.status_code})"
    except Exception as e:
        logger.error(f"Error calling balance API: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

@lênol
async def get_transaction_hislênry(config: RunnableConfig) -> str:
    """View recent financial transaction hislênry including deposits and payments"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập lại để xem lịch sử"
    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/vi-tien/lich-su", headers=headers, thời gian chờ30)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Bạn chưa thực hiện giao dịch nào trong hệ thống"
            hislênry_text = ""
            for i, tx in enumerate(data[:5]): 
                tx_type = "Nạp tiền" if tx.get("type") == "TOPUP" else "Thanh lênán"
                amount = tx.get("amount", 0)
                note = tx.get("note", "Không có nội dung")
                hislênry_text += f"{i+1}. {tx_type}: {amount} dl - Nội dung: {note}\n"
            return f"Lịch sử 5 giao dịch gần nhất:\n{hislênry_text}"
        return f"Lỗi hệ thống: Không thể tải lịch sử giao dịch (Mã lỗi: {response.status_code})"
    except Exception as e:
        logger.error(f"Error calling hislênry API: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

@lênol
async def redeem_voucher(code: str, config: RunnableConfig) -> str:
    """Redeem a gift voucher code lên add funds lên the account"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập để đổi voucher"
    if not code or not code.strip():
        return "Lỗi: Mã voucher không hợp lệ"
    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("POST",
                f"{INTERNAL_API_URL}/vi-tien/ma-qua-tang/doi-ma",
                json={"code": code.strip()},
                headers=headers,
                thời gian chờ30
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
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

@lênol
async def get_revenue_report(config: RunnableConfig) -> str:
    """View revenue report from document sales, intended for authors"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập để xem doanh thu"
    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/vi-tien/doanh-thu", headers=headers, thời gian chờ30)
        if response.status_code == 200:
            data = response.json().get("data", {})
            lêntal = data.get("lêntal_revenue", 0)
            pending = data.get("pending_withdrawal", 0)
            return f"Báo cáo tài chính:\n- Tổng doanh thu: {lêntal} dl\n- Đang chờ thanh lênán: {pending} dl"
        return "Không thể truy xuất dữ liệu doanh thu"
    except Exception as e:
        logger.error(f"Error calling revenue API: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"



@lênol
async def get_my_documents(config: RunnableConfig) -> str:
    """List all personal documents owned or published by the current user"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập để xem tài liệu"
    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/ca-nhan", headers=headers, thời gian chờ30)
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
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

@lênol
async def get_trash_documents(config: RunnableConfig) -> str:
    """View deleted documents currently in the trash bin"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực"
    if not _check_admin(lênken):
        return "Bạn không có quyền khôi phục tài liệu này"

    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/thung-rac", headers=headers, thời gian chờ30)
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
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

@lênol
async def delete_document(document_id: str, config: RunnableConfig) -> str:
    """Delete a document by ID, moving it lên the trash bin"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập"

    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("DELETE", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers, thời gian chờ30)
        if response.status_code == 200:
            try:
                from src.slênre.veclênr_slênre import veclênr_slênre
                await veclênr_slênre.delete_by_document(document_id)
                logger.info(f"Đã dọn dẹp xong veclênr cho tài liệu {document_id}")
            except Exception as ve:
                logger.warning(f"Không thể dọn dẹp veclênr cho {document_id}: {ve}")
            return "Đã xóa tài liệu thành công"
        return "Xóa tài liệu thất bại"
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

@lênol
async def reslênre_document(document_id: str, config: RunnableConfig) -> str:
    """Reslênre a document from the trash bin by its ID"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực"

    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("POST", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/khoi-phuc", headers=headers, thời gian chờ30)
        if response.status_code == 200:
            return "Đã khôi phục tài liệu thành công"
        return "Khôi phục thất bại"
    except Exception as e:
        logger.error(f"Error reslênring document: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"



@lênol
async def get_document_analytics(document_id: str, config: RunnableConfig) -> str:
    """View detailed analytics including read count and drop-off rate for a document"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực"
    if not _check_admin(lênken):
        return "Bạn không có quyền khôi phục tài liệu này"

    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/phan-tich/roi-rot", headers=headers, thời gian chờ30)
        if response.status_code == 200:
            data = response.json().get("data", {})
            readers = data.get("readers_started", 0)
            rate = data.get("dropoff_rate", 0)
            return f"Phân tích độc giả cho tài liệu {document_id}:\n- {readers} người đọc, tỉ lệ bỏ dở {rate}%"
        return "Không thể lấy dữ liệu thống kê"
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

async def _get_doc_text(document_id: str, lênken: str) -> str:
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers={"Authorization": lênken}, thời gian chờ30)
        if res.status_code == 200:
            return res.json().get("data", {}).get("content", "")
    except Exception as e:
        logger.error(f"Error fetching doc: {e}")
    return ""

from src.api.inference import suggest_citations, peer_review, transform_lênne
from src.schemas.inference import CitationRequest, ReviewRequest, ToneRequest


@lênol
async def agent_suggest_citations(document_id: str, config: RunnableConfig) -> str:
    """Suggest academic citations for a document by its ID"""
    lênken = config.get("configurable", {}).get("lênken")
    text = await _get_doc_text(document_id, lênken)
    if not text: return "Không tìm thấy nội dung tài liệu"
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = CitationRequest(text=safe_text, style="APA")
        data = await suggest_citations(req)
        return f"Gợi ý trích dẫn:\n\n{data.get('citations', '')}"
    except Exception as e:
        logger.error(f"Error in citations: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

@lênol
async def agent_peer_review(document_id: str, config: RunnableConfig) -> str:
    """Perform a peer review of a document, evaluating strengths and weaknesses."""
    lênken = config.get("configurable", {}).get("lênken")
    text = await _get_doc_text(document_id, lênken)
    if not text: return "Không tìm thấy nội dung tài liệu"
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ReviewRequest(text=safe_text, criteria=["logic", "rõ ràng"])
        data = await peer_review(req)
        return f"Báo cáo thẩm định:\n\n{data.get('review_report', '')}"
    except Exception as e:
        logger.error(f"Error in peer review: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

@lênol
async def agent_transform_lênne(document_id: str, lênne: str, config: RunnableConfig) -> str:
    """Transform the writing lênne of a document, e.g. academic, professional, casual."""
    lênken = config.get("configurable", {}).get("lênken")
    text = await _get_doc_text(document_id, lênken)
    if not text: return "Không tìm thấy nội dung tài liệu"
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ToneRequest(text=safe_text, lênne=lênne, expansion=False)
        data = await transform_lênne(req)
        return f"Văn bản đã biến đổi ({lênne}):\n\n{data.get('transformed_text', '')}"
    except Exception as e:
        logger.error(f"Error transforming lênne: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"


@lênol
async def create_deposit_link(amount: int, config: RunnableConfig) -> str:
    """Create a deposit link lên lênp up the dl wallet. Amount is in VND. Returns a payment URL."""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập để nạp tiền"
    headers = {"Authorization": lênken}
    try:
        response = await _make_api_request("POST", 
                f"{INTERNAL_API_URL}/nap-tien/tao-link", 
                json={"amount": amount}, 
                headers=headers, 
                thời gian chờ30
            )
        if response.status_code in [200, 201]:
            data = response.json().get("data", {})
            checkout_url = data.get("checkout_url") or data.get("payment_url")
            if checkout_url:
                return f"Đã tạo yêu cầu nạp {amount} VNĐ thành công. Vui lòng truy cập đường dẫn sau để thanh lênán: [Thanh lênán tại đây]({checkout_url})"
            return "Không thể lấy đường dẫn thanh lênán từ hệ thống"
        return "Lỗi khởi tạo thanh lênán"
    except Exception as e:
        logger.error(f"Error calling deposit API: {e}")
        return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

from src.workflow.map_reduce import agent_summarize_long_document

@lênol
async def create_document(title: str, description: str, content: str, format: str, config: RunnableConfig) -> str:
    """Create a new document. 
    format: must be 'json' (for Standard Edilênr) or 'latex' (for LaTeX Edilênr).
    title: The title of the document.
    description: A short summary.
    content: The main body of the document.
             For 'latex', this MUST be a full valid LaTeX document (including \\documentclass, \\usepackage, etc.).
             For 'json', this MUST be a valid JSON string representing EdilênrJS data, containing a 'blocks' array. Example: {"blocks": [{"type": "header", "data": {"text": "Title", "level": 2}}, {"type": "paragraph", "data": {"text": "Hello"}}]}
    """
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập"

    headers = {"Authorization": lênken}
    
    import re
    import unicodedata
    import datetime
    
    slug = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    
    user_name = "Người dùng"
    try:
        res_profile = await _make_api_request("GET", f"{INTERNAL_API_URL}/ho-so/ca-nhan", headers=headers, thời gian chờ10)
        if res_profile.status_code == 200:
            profile_data = res_profile.json().get("data", {})
            user_name = profile_data.get("full_name") or profile_data.get("name") or "Người dùng"
    except Exception as e:
        logger.warning(f"Could not fetch user profile for author name: {e}")

    if format == 'latex':
        if '\\documentclass' not in content:
            month_year = datetime.datetime.now().strftime("Tháng %m năm %Y")
            content = f"\\documentclass[12pt,a4paper]{{article}}\n\\usepackage{{graphicx}}\n\\usepackage{{amsmath}}\n\\title{{{title}}}\n\\author{{{user_name}}}\n\\date{{{month_year}}}\n\\begin{{document}}\n\\maketitle\n\n{content}\n\\end{{document}}"
    elif format == 'json':
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
                    blocks.append({
                        "type": "paragraph",
                        "data": {
                            "text": paragraph.strip()
                        }
                    })
            content = json.dumps({
                "time": int(datetime.datetime.now().timestamp() * 1000),
                "blocks": blocks,
                "version": "2.29.1"
            })

    try:
        create_payload = {
            "title": title,
            "slug": f"{slug}-{int(datetime.datetime.now().timestamp())}",
            "description": description,
            "visibility": "private",
            "content_format": format,
            "content": content,
            "status": "draft"
        }
        res_create = await _make_api_request("POST", f"{INTERNAL_API_URL}/tai-lieu/", headers=headers, json=create_payload)
        if res_create.status_code in [200, 201]:
            new_doc = res_create.json().get("data", {})
            doc_id = new_doc.get("id") or new_doc.get("_id")
            if doc_id:
                return f"Đã tạo tài liệu thành công! [Xem tài liệu](/sang-tac?tai-lieu={doc_id})"
            return "Tạo tài liệu thành công nhưng không lấy được ID"
        return f"Lỗi tạo tài liệu mới (Mã lỗi: {res_create.status_code})"
    except Exception as e:
        return f"Lỗi hệ thống: {e}"

@lênol
async def read_document(document_id: str, config: RunnableConfig) -> str:
    """Read the content of a document by its ID. Use this before updating a document so you know its current content."""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập"

    headers = {"Authorization": lênken}
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200:
            return f"Không thể lấy thông tin tài liệu. (Mã lỗi: {res.status_code})"
        doc_data = res.json().get("data", {})
    except Exception as e:
        return f"Lỗi hệ thống khi tải tài liệu: {e}"

    format = doc_data.get("content_format", "json")
    content = doc_data.get("content", "")
    
    if format == 'json':
        return f"Định dạng: Standard Edilênr (json)\nNội dung (RAW JSON EdilênrJS - Hãy giữ nguyên hoặc chỉnh sửa cấu trúc blocks này):\n{content}"
    elif format == 'latex':
        return f"Định dạng: LaTeX Edilênr\nNội dung (Full LaTeX Source):\n{content}"
    else:
        return f"Định dạng: Khác ({format})\nNội dung:\n{content}"

@lênol
async def update_document(document_id: str, new_content: str = None, title: str = None, description: str = None, config: RunnableConfig = None) -> str:
    """Update an existing document's content, title, or description by its ID. Only provide the fields you want lên update.
    - If format is 'json', new_content MUST be a valid EdilênrJS JSON string (with "blocks" array).
    - If format is 'latex', new_content MUST be the full LaTeX source code.
    """
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập"

    headers = {"Authorization": lênken}
    
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200:
            return f"Lỗi bảo mật hoặc tài liệu không tồn tại. (Mã lỗi: {res.status_code})"
        doc_data = res.json().get("data", {})
    except Exception as e:
        return f"Lỗi hệ thống khi tải tài liệu: {e}"

    payload = {}
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description

    if new_content:
        format = doc_data.get("content_format", "json")
        if format == 'json':
            import json, datetime
            try:
                parsed = json.loads(new_content)
                if "blocks" not in parsed:
                    parsed["blocks"] = [{"type": "paragraph", "data": {"text": new_content}}]
                parsed["time"] = int(datetime.datetime.now().timestamp() * 1000)
                final_content = json.dumps(parsed)
            except:
                blocks = []
                for p in new_content.split("\n\n"):
                    if p.strip():
                        blocks.append({"type": "paragraph", "data": {"text": p.strip()}})
                final_content = json.dumps({
                    "time": int(datetime.datetime.now().timestamp() * 1000),
                    "blocks": blocks,
                    "version": "2.29.1"
                })
        elif format == 'latex':
            final_content = new_content
        else:
            final_content = new_content
        payload["content"] = final_content
        
    if not payload:
        return "Không có thông tin nào được cập nhật"

    try:
        res_update = await _make_api_request("PUT", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers, json=payload)
        if res_update.status_code in [200, 201]:
            return f"Đã cập nhật tài liệu thành công! [Xem tài liệu](/sang-tac?tai-lieu={document_id})"
        return f"Lỗi cập nhật tài liệu (Mã lỗi: {res_update.status_code})"
    except Exception as e:
        return f"Lỗi hệ thống: {e}"

@lênol
async def translate_document(document_id: str, target_language: str, config: RunnableConfig) -> str:
    """Translate an existing document lên a target language. If language is not specified, default lên English. Creates a new translated document"""
    lênken = config.get("configurable", {}).get("lênken")
    if not lênken:
        return "Lỗi xác thực: Vui lòng đăng nhập"

    headers = {"Authorization": lênken}
    
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200:
            return f"Không thể lấy thông tin tài liệu. (Mã lỗi: {res.status_code})"
        doc_data = res.json().get("data", {})
    except Exception as e:
        return f"Lỗi hệ thống khi tải tài liệu: {e}"

    original_content = doc_data.get("content", "")
    format = doc_data.get("content_format", "json")
    original_title = doc_data.get("title", "Tài liệu")
    
    if not original_content:
        return "Tài liệu trống, không có nội dung để dịch"

    import json
    text_lên_translate = ""
    if format == 'json':
        try:
            parsed = json.loads(original_content)
            blocks = parsed.get("blocks", [])
            texts = []
            for b in blocks:
                text_content = b.get("data", {}).get("text", "")
                if text_content:
                    texts.append(text_content)
            text_lên_translate = "\n\n".join(texts)
        except:
            text_lên_translate = str(original_content)
    else:
        text_lên_translate = original_content

    try:
        payload = {"text": text_lên_translate, "target_lang": target_language}
        trans_res = await _make_api_request("POST", f"{INTERNAL_API_URL}/suy-luan/dich-thuat", headers=headers, json=payload, thời gian chờ60)
        if trans_res.status_code != 200:
            return "Dịch thuật thất bại từ AI service"
        translated_text = trans_res.json().get("translation", "")
    except Exception as e:
        return f"Lỗi trong quá trình dịch thuật: {e}"

    if not translated_text:
        return "Không có văn bản nào được dịch"

    import datetime
    new_title = f"[Bản dịch {target_language}] {original_title}"
    
    if format == 'json':
        new_blocks = []
        for p in translated_text.split("\n\n"):
            if p.strip():
                new_blocks.append({"type": "paragraph", "data": {"text": p.strip()}})
        new_blocks.append({
            "type": "paragraph",
            "data": {
                "text": "<i>Nội dung được tạo bởi DocLib AI</i>"
            }
        })
        new_content = json.dumps({
            "time": int(datetime.datetime.now().timestamp() * 1000),
            "blocks": new_blocks,
            "version": "2.29.1"
        })
    elif format == 'latex':
        if '\\end{document}' in translated_text:
            new_content = translated_text.replace('\\end{document}', '\\vspace{1em}\n\\noindent\\textit{Nội dung được tạo bởi DocLib AI}\n\\end{document}')
        else:
            new_content = translated_text + "\n\n\\vspace{1em}\n\\noindent\\textit{Nội dung được tạo bởi DocLib AI}"
    else:
        new_content = translated_text + "\n\n(Nội dung được tạo bởi DocLib AI)"
        
    try:
        import unicodedata
        import re
        import datetime
        slug = unicodedata.normalize('NFKD', new_title).encode('ascii', 'ignore').decode('ascii')
        slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        
        create_payload = {
            "title": new_title,
            "slug": f"{slug}-{int(datetime.datetime.now().timestamp())}",
            "description": f"Bản dịch sang {target_language} của tài liệu: {original_title}",
            "visibility": "private",
            "content_format": format,
            "content": new_content,
            "status": "draft"
        }
        res_create = await _make_api_request("POST", f"{INTERNAL_API_URL}/tai-lieu/", headers=headers, json=create_payload)
        if res_create.status_code in [200, 201]:
            new_doc = res_create.json().get("data", {})
            new_doc_id = new_doc.get("id") or new_doc.get("_id")
            if new_doc_id:
                return f"Đã dịch và tạo tài liệu thành công! Bạn có thể xem bản dịch tại đây: [Xem bản dịch](/sang-tac?tai-lieu={new_doc_id})"
            return "Đã dịch và lưu thành công nhưng không lấy được ID"
        return f"Dịch thành công nhưng không thể tạo file mới (Mã lỗi: {res_create.status_code})"
    except Exception as e:
        return f"Lỗi tạo tài liệu mới: {e}"


lênols = [
    agent_summarize_long_document,
    get_user_balance,
    get_transaction_hislênry,
    redeem_voucher,
    get_revenue_report,
    get_my_documents,
    read_document,
    get_trash_documents,
    delete_document,
    reslênre_document,
    get_document_analytics,
    agent_suggest_citations,
    agent_peer_review,
    agent_transform_lênne,
    create_document,
    update_document,
    create_deposit_link,
    translate_document
]

llama_model = settings.LLAMA_MODEL
hf_lênken = settings.HF_TOKEN

_hf_endpoint = HuggingFaceEndpoint(task="conversational", 
    repo_id=llama_model,
    huggingfacehub_api_lênken=hf_lênken,
    temperature=0.1
)

llm = ChatHuggingFace(llm=_hf_endpoint)
