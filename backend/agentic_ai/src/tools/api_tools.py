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
        from core.config import settings

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        role = payload.get("role", "guest")
        return role == "admin"
    except:
        return False


from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.prebuilt import create_react_agent
from loguru import logger

from core.config import settings

INTERNAL_API_URL = settings.INTERNAL_API_URL


@tool
async def get_user_balance(config: RunnableConfig) -> str:
    """Get the current user's DocLib wallet balance in dl currency"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to proceed with this specific operation please log in and try again"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/wallets/balance",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            balance = data.get("balance", 0)
            return f"Your current account balance is {balance} credits"
        elif response.status_code == 401:
            return "The current user session has expired and authentication must be renewed"
        raise Exception("Lỗi tải số dư tài khoản")
    except Exception:
        logger.exception("Lỗi truy cập dữ liệu số dư")
        raise Exception("Error occurred, please retry")


@tool
async def get_transaction_history(config: RunnableConfig) -> str:
    """View recent financial transaction history including deposits and payments"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required to view transaction history"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/wallets/transactions",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "No recent transactions found"
            history_text = ""
            for i, tx in enumerate(data[:5]):
                tx_type = "Deposit" if tx.get("type") == "TOPUP" else "Payment"
                amount = tx.get("amount", 0)
                note = tx.get("note", "No content")
                history_text += f"{i+1} {tx_type} transaction of {amount} credits with note {note}\n"
            return f"Below is the history of your recent transactions\n{history_text}"
        return "Failed to load transaction history"
    except Exception:
        logger.exception("Lỗi tải lịch sử giao dịch")
        raise Exception("Error occurred, please retry")


@tool
async def redeem_voucher(code: str, config: RunnableConfig) -> str:
    """Redeem a gift voucher code to add funds to the account"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required to redeem gift code"
    if not code or not code.strip():
        return "Gift code invalid or already redeemed"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/coupons/redeem",
            json={"code": code.strip()},
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            res_data = response.json().get("data", {})
            bonus = res_data.get("bonus_dl", 0)
            return f"The gift code was redeemed successfully and your account has been credited with {bonus} credits"
        return "Gift code redemption failed"
    except Exception:
        logger.exception("Lỗi xử lý yêu cầu đổi thưởng")
        raise Exception("Error occurred, please retry")


@tool
async def get_revenue_report(config: RunnableConfig) -> str:
    """View revenue report from document sales, intended for authors"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required to view revenue report"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/withdrawals/revenue",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            total = data.get("total_revenue", 0)
            pending = data.get("pending_withdrawal", 0)
            return f"The financial report indicates a total revenue of {total} currency units with {pending} units pending withdrawal"
        return "Failed to retrieve revenue data"
    except Exception:
        logger.exception("Lỗi tải báo cáo doanh thu")
        raise Exception("Error occurred, please retry")


@tool
async def get_my_documents(config: RunnableConfig) -> str:
    """List all personal documents owned or published by the current user"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required to view document library"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/documents/personal",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "No documents in library"
            res = "Here is the list of your available documents\n"
            for doc in data:
                res += f"Document {doc.get('title')} is currently in {doc.get('status')} status\n"
            return res
        return "Failed to fetch document list"
    except Exception:
        logger.exception("Lỗi tải danh sách tài liệu")
        raise Exception("Error occurred, please retry")


@tool
async def get_trash_documents(config: RunnableConfig) -> str:
    """View deleted documents currently in the trash bin"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required"
    if not _check_system_access(token):
        return "Access denied: insufficient authorization"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/documents/trash",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Trash bin is empty"
            res = "The following documents are located within the trash bin\n"
            for doc in data:
                res += f"Document {doc.get('title')} was deleted on {doc.get('deleted_at')}\n"
            return res
        return "Failed to access trash bin"
    except Exception:
        logger.exception("Lỗi tải danh sách mục đã xóa")
        raise Exception("Error occurred, please retry")


@tool
async def delete_document(document_id: str, config: RunnableConfig) -> str:
    """Delete a document by ID, moving it to the trash bin"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required to delete document"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "DELETE",
            f"{INTERNAL_API_URL}/documents/{document_id}",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            try:
                from src.store.vector_store import vector_store

                await vector_store.delete_by_document(document_id)
                logger.info("Dọn dẹp chỉ mục tài liệu thành công")
            except Exception:
                logger.warning("Lỗi dọn dẹp chỉ mục tài liệu")
            return "Document deleted successfully"
        return "Failed to delete document"
    except Exception:
        logger.exception("Lỗi xóa tài liệu")
        raise Exception("Error occurred, please retry")


@tool
async def restore_document(document_id: str, config: RunnableConfig) -> str:
    """Restore a document from the trash bin by its ID"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/documents/{document_id}/restore",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            return "Document restored successfully"
        return "Document restoration failed"
    except Exception:
        logger.exception("Lỗi khôi phục tài liệu")
        raise Exception("Error occurred, please retry")


@tool
async def get_document_analytics(document_id: str, config: RunnableConfig) -> str:
    """View detailed analytics including read count and drop-off rate for a document"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required"
    if not _check_system_access(token):
        return "Operation denied: insufficient authorization"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/documents/{document_id}/analyze/dropoff",
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            readers = data.get("readers_started", 0)
            rate = data.get("dropoff_rate", 0)
            return f"The audience analysis indicates {readers} readers with a bounce rate of {rate} percent"
        return "Failed to retrieve statistical data"
    except Exception:
        logger.exception("Lỗi truy xuất dữ liệu phân tích")
        raise Exception("Error occurred, please retry")


async def _get_doc_text(document_id: str, token: str) -> str:
    try:
        res = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/documents/{document_id}",
            headers={"Authorization": token},
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if res.status_code == 200:
            return res.json().get("data", {}).get("content", "")
    except Exception:
        logger.error("Lỗi tải nội dung tài liệu")
    return ""


from src.router.inference import peer_review, suggest_citations, transform_tone

from core.schemas.inference import CitationRequest, ReviewRequest, ToneRequest


@tool
async def agent_suggest_citations(document_id: str, config: RunnableConfig) -> str:
    """Suggest academic citations for a document by its ID"""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Document content not found"
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.DEFAULT_CHUNK_SIZE * 2, chunk_overlap=0
    )
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = CitationRequest(text=safe_text, style="APA")
        data = await suggest_citations(req)
        return f"Here are the suggested citations for the document\n\n{data.get('citations', '')}"
    except Exception:
        logger.exception("Lỗi tạo gợi ý trích dẫn")
        raise Exception("Error occurred, please retry")


@tool
async def agent_peer_review(document_id: str, config: RunnableConfig) -> str:
    """Perform a peer review of a document, evaluating strengths and weaknesses"""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Document content not found"
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.DEFAULT_CHUNK_SIZE * 4, chunk_overlap=0
    )
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ReviewRequest(text=safe_text, criteria=["logic", "clear"])
        data = await peer_review(req)
        return f"Here is the peer review report for the document\n\n{data.get('review_report', '')}"
    except Exception:
        logger.exception("Lỗi quá trình đánh giá chéo")
        raise Exception("Error occurred, please retry")


@tool
async def agent_transform_tone(
    document_id: str, tone: str, config: RunnableConfig
) -> str:
    """Transform the writing tone of a document, e.g. academic, professional, casual"""
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Document content not found"
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.DEFAULT_CHUNK_SIZE * 2, chunk_overlap=0
    )
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ToneRequest(text=safe_text, tone=tone, expansion=False)
        data = await transform_tone(req)
        return f"Here is the transformed text matching the requested tone\n\n{data.get('transformed_text', '')}"
    except Exception:
        logger.exception("Lỗi thay đổi giọng văn")
        raise Exception("Error occurred, please retry")


@tool
async def create_deposit_link(amount: int, config: RunnableConfig) -> str:
    """Create a deposit link to top up the dl wallet. Amount is in VND. Returns a payment URL"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required to initiate deposit"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/deposits",
            json={"amount": amount},
            headers=headers,
            timeout=settings.LONG_PROCESS_TIMEOUT,
        )
        if response.status_code in [200, 201]:
            data = response.json().get("data", {})
            checkout_url = data.get("checkout_url") or data.get("payment_url")
            if checkout_url:
                return f"A deposit request for {amount} currency units has been created please visit the following link to proceed with the payment [Pay here]({checkout_url}/)"
            return "Failed to generate payment link"
        return "Payment initialization failed"
    except Exception:
        logger.exception("Lỗi xử lý yêu cầu nạp tiền")
        raise Exception("Error occurred, please retry")


from src.workflow.map_reduce import agent_summarize_long_document


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
        return "Authentication required"

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
            f"{INTERNAL_API_URL}/profile/me",
            headers=headers,
            timeout=settings.DEFAULT_HTTP_TIMEOUT,
        )
        if res_profile.status_code == 200:
            profile_data = res_profile.json().get("data", {})
            user_name = (
                profile_data.get("full_name") or profile_data.get("name") or "User"
            )
    except Exception:
        logger.warning("Lỗi tải hồ sơ người dùng để lấy thông tin tác giả")

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
            f"{INTERNAL_API_URL}/documents/",
            headers=headers,
            json=create_payload,
        )
        if res_create.status_code in [200, 201]:
            new_doc = res_create.json().get("data", {})
            doc_id = new_doc.get("id") or new_doc.get("_id")
            if doc_id:
                return f"The new document was created successfully [View document](/editor?document_id={doc_id})"
            return "Document created but identifier unavailable"
        return "Failed to create document"
    except Exception:
        raise Exception("Processing error")


@tool
async def read_document(document_id: str, config: RunnableConfig) -> str:
    """Read the content of a document by its ID. Use this before updating a document so you know its current content"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required"

    headers = {"Authorization": token}
    try:
        res = await _make_api_request(
            "GET", f"{INTERNAL_API_URL}/documents/{document_id}", headers=headers
        )
        if res.status_code != 200:
            return "Failed to retrieve document info"
        doc_data = res.json().get("data", {})
    except Exception:
        raise Exception("Lỗi tải tài liệu")

    format = doc_data.get("content_format", "json")
    content = doc_data.get("content", "")

    if format == "json":
        return f"The document utilizes the standard editor format with the following content\n{content}"
    elif format == "latex":
        return f"The document utilizes the mathematical editor format with the following content\n{content}"
    else:
        return f"The document utilizes an alternative format with the following content\n{content}"


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
        return "Authentication required"

    headers = {"Authorization": token}

    try:
        res = await _make_api_request(
            "GET", f"{INTERNAL_API_URL}/documents/{document_id}", headers=headers
        )
        if res.status_code != 200:
            return "Operation failed: security restriction or document missing"
        doc_data = res.json().get("data", {})
    except Exception:
        raise Exception("Lỗi tải tài liệu")

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
        return "No modifications made to document"

    try:
        res_update = await _make_api_request(
            "PUT",
            f"{INTERNAL_API_URL}/documents/{document_id}",
            headers=headers,
            json=payload,
        )
        if res_update.status_code in [200, 201]:
            return f"The document was updated successfully [View document](/editor?document_id={document_id})"
        raise Exception("Lỗi cập nhật tài liệu")
    except Exception:
        raise Exception("Processing error")


@tool
async def translate_document(
    document_id: str, target_language: str, config: RunnableConfig
) -> str:
    """Translate an existing document to a target language. If language is not specified, default to English. Creates a new translated document"""
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication required"

    headers = {"Authorization": token}

    try:
        res = await _make_api_request(
            "GET", f"{INTERNAL_API_URL}/documents/{document_id}", headers=headers
        )
        if res.status_code != 200:
            return "Failed to retrieve document info"
        doc_data = res.json().get("data", {})
    except Exception:
        raise Exception("Lỗi tải tài liệu")

    original_content = doc_data.get("content", "")
    format = doc_data.get("content_format", "json")
    original_title = doc_data.get("title", "Document")

    if not original_content:
        return "Document contains no text for translation"

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
            f"{INTERNAL_API_URL}/inference/translate",
            headers=headers,
            json=payload,
            timeout=60,
        )
        if trans_res.status_code != 200:
            return "Translation service failed"
        translated_text = trans_res.json().get("translation", "")
    except Exception:
        return "Translation process failed"

    if not translated_text:
        return "Failed to generate translation"

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
            f"{INTERNAL_API_URL}/documents/",
            headers=headers,
            json=create_payload,
        )
        if res_create.status_code in [200, 201]:
            new_doc = res_create.json().get("data", {})
            new_doc_id = new_doc.get("id") or new_doc.get("_id")
            if new_doc_id:
                return f"The translation was generated and saved successfully you can access it here [View translation](/editor?document_id={new_doc_id})"
            return "Translation generated but file identifier unavailable"
        return "Translation generated but save failed"
    except Exception:
        return "Failed to create translated document"


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
