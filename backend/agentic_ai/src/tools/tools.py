import asyncio
import datetime
import json
import re
import unicodedata
from typing import Optional
import httpx
import jwt
from core.config import settings
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from src.router.inference import peer_review, suggest_citations, transform_tone
from src.workflow.map_reduce import agent_summarize_long_document
from uuid6 import uuid7

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

def _check_system_access(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("role", "guest") == "admin"
    except Exception:
        return False

@tool(description="Get the current user DocLib wallet balance in digital currency units")
async def get_user_balance(config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        response = await _make_api_request("GET", f"{settings.FINANCE_URL}/vi-tien/so-du", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            return f"Your current authenticated account operational balance is {response.json().get('data', {}).get('balance', 0)} credits"
        if response.status_code == 401:
            return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
        return "Lỗi xử lý tài khoản"
    except Exception:
        logger.error("Mất kết nối mạng tạm thời")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="View recent financial transaction history including system deposits and payments")
async def get_transaction_history(config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        response = await _make_api_request("GET", f"{settings.FINANCE_URL}/vi-tien/giao-dich", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
            history = "".join([f"{i+1} {'Deposit' if tx.get('type') == 'TOPUP' else 'Payment'} transaction of {tx.get('amount', 0)} credits regarding {tx.get('note', 'No details')}\n" for i, tx in enumerate(data[:5])])
            return f"Below is the detailed history of your recent financial transactions\n{history}"
        return "Lỗi xử lý tài khoản"
    except Exception:
        logger.error("Lỗi xử lý tài khoản")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Redeem a gift voucher code to add funds to the current account")
async def redeem_voucher(code: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    if not code or not code.strip():
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"
    try:
        response = await _make_api_request("POST", f"{settings.FINANCE_URL}/giam-gia/doi-thuong", json={"code": code.strip()}, headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            return f"The gift code was redeemed successfully providing {response.json().get('data', {}).get('bonus_dl', 0)} credits"
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"
    except Exception:
        logger.error("Lỗi xử lý tài khoản")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="View revenue report from document sales intended for author accounts")
async def get_revenue_report(config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        response = await _make_api_request("GET", f"{settings.FINANCE_URL}/rut-tien/doanh-thu", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", {})
            return f"The financial report indicates a total revenue of {data.get('total_revenue', 0)} currency units"
        return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="List all personal documents owned or published by the authenticated user")
async def get_my_documents(config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        response = await _make_api_request("GET", f"{settings.CONTENT_URL}/tai-lieu/ca-nhan", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Lỗi khi truy xuất tài liệu"
            return "Lỗi khi truy xuất tài liệu" + "".join([f"Document {d.get('title')} is currently in {d.get('status')} status\n" for d in data])
        return "Lỗi khi truy xuất tài liệu"
    except Exception:
        logger.error("Lỗi khi truy xuất tài liệu")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="View deleted documents currently stored in the system trash bin")
async def get_trash_documents(config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token or not _check_system_access(token):
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        response = await _make_api_request("GET", f"{settings.CONTENT_URL}/tai-lieu/thung-rac", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
            return "Lỗi khi truy xuất tài liệu" + "".join([f"Document {d.get('title')} was deleted on {d.get('deleted_at')}\n" for d in data])
        return "Lỗi truy xuất cơ sở dữ liệu hệ thống"
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Delete a document by identifier moving it to the trash bin")
async def delete_document(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        response = await _make_api_request("DELETE", f"{settings.CONTENT_URL}/tai-lieu/{document_id}", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            try:
                from src.store.vector_store import vector_store
                await vector_store.delete_by_document(document_id)
                logger.info("Khởi tạo danh mục tìm kiếm thành công")
            except Exception:
                logger.warning("Lỗi truy xuất cơ sở dữ liệu hệ thống")
            return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
        return "Khởi tạo AI thành công"
    except Exception:
        logger.error("Lỗi khi truy xuất tài liệu")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Restore a deleted document from the trash bin by its identifier")
async def restore_document(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        response = await _make_api_request("POST", f"{settings.CONTENT_URL}/tai-lieu/{document_id}/khoi-phuc", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
        return "Lỗi khi truy xuất tài liệu"
    except Exception:
        logger.error("Lỗi khi truy xuất tài liệu")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="View detailed structural analytics including read count and dropoff rate for a document")
async def get_document_analytics(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token or not _check_system_access(token):
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        response = await _make_api_request("GET", f"{settings.CONTENT_URL}/tai-lieu/{document_id}/phan-tich/roi-bo", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", {})
            return f"The audience analysis indicates {data.get('readers_started', 0)} readers with a bounce rate of {data.get('dropoff_rate', 0)} percent"
        return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

async def _get_doc_text(document_id: str, token: str) -> str:
    try:
        res = await _make_api_request("GET", f"{settings.CONTENT_URL}/tai-lieu/{document_id}", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if res.status_code == 200:
            return res.json().get("data", {}).get("content", "")
    except Exception:
        logger.error("Lỗi khi truy xuất tài liệu")
    return ""

@tool(description="Suggest structured academic citations for a specified document by its identifier")
async def agent_suggest_citations(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    safe_text = RecursiveCharacterTextSplitter(chunk_size=settings.DEFAULT_CHUNK_SIZE * 2, chunk_overlap=0).split_text(text)[0] if text else ""
    try:
        data = await suggest_citations(CitationRequest(text=safe_text, style="APA"))
        return f"Here are the suggested structural citations for the specified operational document\n\n{data.get('citations', '')}"
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Perform a structural peer review evaluating designated strengths and weaknesses")
async def agent_peer_review(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    safe_text = RecursiveCharacterTextSplitter(chunk_size=settings.DEFAULT_CHUNK_SIZE * 4, chunk_overlap=0).split_text(text)[0] if text else ""
    try:
        data = await peer_review(ReviewRequest(text=safe_text, criteria=["logic", "clear"]))
        return f"Here is the detailed structural peer review report for the document\n\n{data.get('review_report', '')}"
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Transform the writing tone of a document representing specific required stylistic output")
async def agent_transform_tone(document_id: str, tone: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    safe_text = RecursiveCharacterTextSplitter(chunk_size=settings.DEFAULT_CHUNK_SIZE * 2, chunk_overlap=0).split_text(text)[0] if text else ""
    try:
        data = await transform_tone(ToneRequest(text=safe_text, tone=tone, expansion=False))
        return f"Here is the transformed text precisely matching the requested stylistic tone\n\n{data.get('transformed_text', '')}"
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Create a secure deposit link to top up the digital wallet balance")
async def create_deposit_link(amount: int, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        response = await _make_api_request("POST", f"{settings.FINANCE_URL}/nap-tien", json={"amount": amount}, headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code in [200, 201]:
            url = response.json().get("data", {}).get("checkout_url") or response.json().get("data", {}).get("payment_url")
            if url:
                return f"A secured deposit request for {amount} currency units was generated successfully please visit the following link to proceed with payment [Pay here]({url}/)"
            return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"
    except Exception:
        logger.error("Mất kết nối mạng tạm thời")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Create a new structural document dynamically mapping specific format parameters")
async def create_document(title: str, description: str, content: str, format: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    slug = re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")).strip().lower())
    try:
        if format == "latex" and "\\documentclass" not in content:
            content = f"\\documentclass[12pt,a4paper]{{article}}\n\\usepackage{{graphicx}}\n\\usepackage{{amsmath}}\n\\title{{{title}}}\n\\begin{{document}}\n\\maketitle\n\n{content}\n\\end{{document}}"
        elif format == "json":
            try:
                parsed = json.loads(content)
                if "blocks" not in parsed:
                    parsed["blocks"] = [{"type": "paragraph", "data": {"text": content}}]
                content = json.dumps(parsed)
            except Exception:
                content = json.dumps({"blocks": [{"type": "paragraph", "data": {"text": p.strip()}} for p in content.split("\n\n") if p.strip()]})
        
        res = await _make_api_request("POST", f"{settings.CONTENT_URL}/tai-lieu/", headers={"Authorization": token}, json={"title": title, "slug": f"{slug}-{int(datetime.datetime.now().timestamp())}", "description": description, "visibility": "private", "content_format": format, "content": content, "status": "draft"})
        if res.status_code in [200, 201]:
            doc_id = res.json().get("data", {}).get("id") or res.json().get("data", {}).get("_id")
            if doc_id:
                return f"The new operational document was successfully compiled and created [View document](/editor?document_id={doc_id})"
            return "Lỗi khi truy xuất tài liệu"
        return "Khởi tạo AI thành công"
    except Exception:
        logger.error("Lỗi khi truy xuất tài liệu")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Read the internal content structure of a specific document verifying current state")
async def read_document(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        res = await _make_api_request("GET", f"{settings.CONTENT_URL}/tai-lieu/{document_id}", headers={"Authorization": token})
        if res.status_code != 200:
            return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
        data = res.json().get("data", {})
        return f"The targeted document utilizes an authorized structural format executing the following content\n{data.get('content', '')}"
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Update existing document textual content verifying appropriate structural authorization logic")
async def update_document(document_id: str, new_content: str = None, title: str = None, description: str = None, config: RunnableConfig = None) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Hệ thống từ chối yêu cầu do không đủ quyền truy cập"
    try:
        res = await _make_api_request("GET", f"{settings.CONTENT_URL}/tai-lieu/{document_id}", headers={"Authorization": token})
        if res.status_code != 200:
            return "Hệ thống không tìm thấy tài liệu được yêu cầu"
        
        payload = {}
        if title: payload["title"] = title
        if description: payload["description"] = description
        if new_content:
            format = res.json().get("data", {}).get("content_format", "json")
            if format == "json":
                try:
                    parsed = json.loads(new_content)
                    if "blocks" not in parsed:
                        parsed["blocks"] = [{"type": "paragraph", "data": {"text": new_content}}]
                    payload["content"] = json.dumps(parsed)
                except Exception:
                    payload["content"] = json.dumps({"blocks": [{"type": "paragraph", "data": {"text": p.strip()}} for p in new_content.split("\n\n") if p.strip()]})
            else:
                payload["content"] = new_content
        
        if not payload:
            return "Lỗi truy xuất cơ sở dữ liệu hệ thống"
            
        update_res = await _make_api_request("PUT", f"{settings.CONTENT_URL}/tai-lieu/{document_id}", headers={"Authorization": token}, json=payload)
        if update_res.status_code in [200, 201]:
            return f"The specified operational document was securely updated successfully [View document](/editor?document_id={document_id})"
        return "Lỗi khi truy xuất tài liệu"
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

@tool(description="Translate an existing active document to a target structural language environment")
async def translate_document(document_id: str, target_language: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Xác thực tài khoản và phân quyền người dùng thành công"
    try:
        res = await _make_api_request("GET", f"{settings.CONTENT_URL}/tai-lieu/{document_id}", headers={"Authorization": token})
        if res.status_code != 200:
            return "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
        
        doc = res.json().get("data", {})
        if not doc.get("content"):
            return "Lỗi khi truy xuất tài liệu"
            
        text = doc["content"]
        if doc.get("content_format") == "json":
            try:
                text = "\n\n".join([b.get("data", {}).get("text", "") for b in json.loads(text).get("blocks", []) if b.get("data", {}).get("text", "")])
            except Exception: pass
            
        trans_res = await _make_api_request("POST", f"{settings.AGENTIC_AI_URL}/suy-luan/dich-thuat", headers={"Authorization": token}, json={"text": text, "target_lang": target_language}, timeout=60)
        if trans_res.status_code != 200 or not trans_res.json().get("translation"):
            return "Lỗi nghiêm trọng xảy ra trong quá trình xử lý AI"
            
        translated = trans_res.json()["translation"]
        if doc.get("content_format") == "json":
            translated = json.dumps({"blocks": [{"type": "paragraph", "data": {"text": p.strip()}} for p in translated.split("\n\n") if p.strip()] + [{"type": "paragraph", "data": {"text": "<i>Content generated by DocLib AI</i>"}}]})
            
        slug = re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", unicodedata.normalize("NFKD", f"[Translation {target_language}] {doc.get('title')}").encode("ascii", "ignore").decode("ascii")).strip().lower())
        create_res = await _make_api_request("POST", f"{settings.CONTENT_URL}/tai-lieu/", headers={"Authorization": token}, json={"title": f"[Translation {target_language}] {doc.get('title')}", "slug": f"{slug}-{int(datetime.datetime.now().timestamp())}", "description": f"Translation to {target_language}", "visibility": "private", "content_format": doc.get("content_format", "json"), "content": translated, "status": "draft"})
        
        if create_res.status_code in [200, 201]:
            new_id = create_res.json().get("data", {}).get("id") or create_res.json().get("data", {}).get("_id")
            if new_id:
                return f"The linguistic translation was generated and safely archived successfully [View translation](/editor?document_id={new_id})"
            return "Khởi tạo AI thành công"
        return "Lỗi khi truy xuất tài liệu"
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

tools = [
    agent_summarize_long_document, get_user_balance, get_transaction_history, redeem_voucher,
    get_revenue_report, get_my_documents, read_document, get_trash_documents, delete_document,
    restore_document, get_document_analytics, agent_suggest_citations, agent_peer_review,
    agent_transform_tone, create_document, update_document, create_deposit_link, translate_document
]

_hf_endpoint = HuggingFaceEndpoint(task="conversational", repo_id=settings.LLAMA_MODEL, huggingfacehub_api_token=settings.HF_TOKEN, temperature=0.1)
llm = ChatHuggingFace(llm=_hf_endpoint)