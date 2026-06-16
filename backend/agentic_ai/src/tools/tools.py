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
INTERNAL_API_URL = settings.INTERNAL_API_URL

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
        return "Authentication is required to proceed with this specific operation securely"
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/wallets/balance", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            return f"Your current authenticated account operational balance is {response.json().get('data', {}).get('balance', 0)} credits"
        if response.status_code == 401:
            return "The current user session has expired and authentication must be renewed"
        return "The system encountered an unexpected error retrieving the current account balance"
    except Exception:
        logger.error("The system encountered a failure attempting to access balance reporting API")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="View recent financial transaction history including system deposits and payments")
async def get_transaction_history(config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to view the operational transaction history logs securely"
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/wallets/transactions", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "There are no recent financial transactions associated with this authenticated account"
            history = "".join([f"{i+1} {'Deposit' if tx.get('type') == 'TOPUP' else 'Payment'} transaction of {tx.get('amount', 0)} credits regarding {tx.get('note', 'No details')}\n" for i, tx in enumerate(data[:5])])
            return f"Below is the detailed history of your recent financial transactions\n{history}"
        return "The system encountered an unexpected error retrieving the financial transaction history"
    except Exception:
        logger.error("The system encountered an error while fetching the transaction history data")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Redeem a gift voucher code to add funds to the current account")
async def redeem_voucher(code: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to securely redeem the provided gift promotional code"
    if not code or not code.strip():
        return "The provided gift promotional code is invalid or has already been redeemed"
    try:
        response = await _make_api_request("POST", f"{INTERNAL_API_URL}/coupons/redeem", json={"code": code.strip()}, headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            return f"The gift code was redeemed successfully providing {response.json().get('data', {}).get('bonus_dl', 0)} credits"
        return "The promotional gift code redemption process failed due to an unexpected issue"
    except Exception:
        logger.error("The system encountered a structural error attempting to process reward redemption")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="View revenue report from document sales intended for author accounts")
async def get_revenue_report(config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to access the secure author revenue reporting dashboard"
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/withdrawals/revenue", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", {})
            return f"The financial report indicates a total revenue of {data.get('total_revenue', 0)} currency units"
        return "The system was unable to safely retrieve the analytical revenue reporting data"
    except Exception:
        logger.error("The system encountered a technical error attempting to fetch revenue analytical report")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="List all personal documents owned or published by the authenticated user")
async def get_my_documents(config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to view the secured personal document library collection"
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/documents/personal", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "There are no available documents located within your personal operational library"
            return "Here is the list of your available documents\n" + "".join([f"Document {d.get('title')} is currently in {d.get('status')} status\n" for d in data])
        return "The system encountered an unexpected error fetching the operational document list"
    except Exception:
        logger.error("The system encountered a structural error attempting to process document listing")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="View deleted documents currently stored in the system trash bin")
async def get_trash_documents(config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token or not _check_system_access(token):
        return "Your account does not possess the necessary authorization to access this area"
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/documents/trash", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "The system document recycling trash bin is currently completely empty"
            return "The following documents are located within the trash bin\n" + "".join([f"Document {d.get('title')} was deleted on {d.get('deleted_at')}\n" for d in data])
        return "The system encountered an unexpected error accessing the deleted document storage"
    except Exception:
        logger.error("The system encountered an error attempting to retrieve deleted recycling items")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Delete a document by identifier moving it to the trash bin")
async def delete_document(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to delete the specified document securely from storage"
    try:
        response = await _make_api_request("DELETE", f"{INTERNAL_API_URL}/documents/{document_id}", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            try:
                from src.store.vector_store import vector_store
                await vector_store.delete_by_document(document_id)
                logger.info("The system successfully completed the index cleanup for the specified document")
            except Exception:
                logger.warning("The system encountered an issue while attempting to clean up document index")
            return "The specified document was transferred to the recycling bin successfully"
        return "The system failed to safely delete the specified document from the database"
    except Exception:
        logger.error("The system encountered a critical failure during the active document deletion process")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Restore a deleted document from the trash bin by its identifier")
async def restore_document(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to restore the specified document securely from recycling"
    try:
        response = await _make_api_request("POST", f"{INTERNAL_API_URL}/documents/{document_id}/restore", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            return "The specified document was recovered and restored successfully to active storage"
        return "The specified document restoration process failed due to an unexpected technical issue"
    except Exception:
        logger.error("The system encountered a severe failure during the document restoration execution process")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="View detailed structural analytics including read count and dropoff rate for a document")
async def get_document_analytics(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token or not _check_system_access(token):
        return "Your account does not possess the necessary administrative authorization to perform this operation"
    try:
        response = await _make_api_request("GET", f"{INTERNAL_API_URL}/documents/{document_id}/analyze/dropoff", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code == 200:
            data = response.json().get("data", {})
            return f"The audience analysis indicates {data.get('readers_started', 0)} readers with a bounce rate of {data.get('dropoff_rate', 0)} percent"
        return "The system was completely unable to retrieve the statistical analytical tracking data"
    except Exception:
        logger.error("The system encountered a failure while attempting to fetch structural analytical data")
        return "The system encountered an unexpected error and requires you to try again later"

async def _get_doc_text(document_id: str, token: str) -> str:
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/documents/{document_id}", headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if res.status_code == 200:
            return res.json().get("data", {}).get("content", "")
    except Exception:
        logger.error("The system encountered a critical structural failure loading the document text")
    return ""

@tool(description="Suggest structured academic citations for a specified document by its identifier")
async def agent_suggest_citations(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "The specified document operational content could not be successfully located"
    safe_text = RecursiveCharacterTextSplitter(chunk_size=settings.DEFAULT_CHUNK_SIZE * 2, chunk_overlap=0).split_text(text)[0] if text else ""
    try:
        data = await suggest_citations(CitationRequest(text=safe_text, style="APA"))
        return f"Here are the suggested structural citations for the specified operational document\n\n{data.get('citations', '')}"
    except Exception:
        logger.error("The system encountered a failure while generating analytical academic citation suggestions")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Perform a structural peer review evaluating designated strengths and weaknesses")
async def agent_peer_review(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "The specified document operational content could not be successfully located"
    safe_text = RecursiveCharacterTextSplitter(chunk_size=settings.DEFAULT_CHUNK_SIZE * 4, chunk_overlap=0).split_text(text)[0] if text else ""
    try:
        data = await peer_review(ReviewRequest(text=safe_text, criteria=["logic", "clear"]))
        return f"Here is the detailed structural peer review report for the document\n\n{data.get('review_report', '')}"
    except Exception:
        logger.error("The system encountered a critical failure during the automated peer review process")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Transform the writing tone of a document representing specific required stylistic output")
async def agent_transform_tone(document_id: str, tone: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "The specified document operational content could not be successfully located"
    safe_text = RecursiveCharacterTextSplitter(chunk_size=settings.DEFAULT_CHUNK_SIZE * 2, chunk_overlap=0).split_text(text)[0] if text else ""
    try:
        data = await transform_tone(ToneRequest(text=safe_text, tone=tone, expansion=False))
        return f"Here is the transformed text precisely matching the requested stylistic tone\n\n{data.get('transformed_text', '')}"
    except Exception:
        logger.error("The automated linguistic tone transformation process encountered an unexpected critical failure")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Create a secure deposit link to top up the digital wallet balance")
async def create_deposit_link(amount: int, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is strictly required to reliably initiate the deposit security process"
    try:
        response = await _make_api_request("POST", f"{INTERNAL_API_URL}/deposits", json={"amount": amount}, headers={"Authorization": token}, timeout=settings.LONG_PROCESS_TIMEOUT)
        if response.status_code in [200, 201]:
            url = response.json().get("data", {}).get("checkout_url") or response.json().get("data", {}).get("payment_url")
            if url:
                return f"A secured deposit request for {amount} currency units was generated successfully please visit the following link to proceed with payment [Pay here]({url}/)"
            return "The system was structurally unable to properly generate the required payment link"
        return "The secured payment initialization sequence encountered an unexpected critical structural failure"
    except Exception:
        logger.error("The system encountered a significant network failure processing the deposit request")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Create a new structural document dynamically mapping specific format parameters")
async def create_document(title: str, description: str, content: str, format: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to perform this action securely validating creator privileges"
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
        
        res = await _make_api_request("POST", f"{INTERNAL_API_URL}/documents/", headers={"Authorization": token}, json={"title": title, "slug": f"{slug}-{int(datetime.datetime.now().timestamp())}", "description": description, "visibility": "private", "content_format": format, "content": content, "status": "draft"})
        if res.status_code in [200, 201]:
            doc_id = res.json().get("data", {}).get("id") or res.json().get("data", {}).get("_id")
            if doc_id:
                return f"The new operational document was successfully compiled and created [View document](/editor?document_id={doc_id})"
            return "The operational document was effectively created however the system failed retrieving identifier"
        return "The system failed to successfully create the new digital document entity"
    except Exception:
        logger.error("The system encountered a severe error actively writing document architectural metadata")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Read the internal content structure of a specific document verifying current state")
async def read_document(document_id: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is strictly required to perform this analytical reading action securely"
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/documents/{document_id}", headers={"Authorization": token})
        if res.status_code != 200:
            return "The system was fundamentally unable to successfully retrieve the requested document"
        data = res.json().get("data", {})
        return f"The targeted document utilizes an authorized structural format executing the following content\n{data.get('content', '')}"
    except Exception:
        logger.error("The system encountered a significant failure reading the internal structural payload")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Update existing document textual content verifying appropriate structural authorization logic")
async def update_document(document_id: str, new_content: str = None, title: str = None, description: str = None, config: RunnableConfig = None) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to update the specified operational document records securely"
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/documents/{document_id}", headers={"Authorization": token})
        if res.status_code != 200:
            return "The operational update failed due to structural restrictions verifying target document existence"
        
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
            return "No valid modifications were structurally detected requiring document mapping database updates"
            
        update_res = await _make_api_request("PUT", f"{INTERNAL_API_URL}/documents/{document_id}", headers={"Authorization": token}, json=payload)
        if update_res.status_code in [200, 201]:
            return f"The specified operational document was securely updated successfully [View document](/editor?document_id={document_id})"
        return "The system encountered an unexpected error processing the targeted document update"
    except Exception:
        logger.error("The system encountered a structural error executing the metadata update operation")
        return "The system encountered an unexpected error and requires you to try again later"

@tool(description="Translate an existing active document to a target structural language environment")
async def translate_document(document_id: str, target_language: str, config: RunnableConfig) -> str:
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Authentication is required to safely initiate the internal linguistic translation execution"
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/documents/{document_id}", headers={"Authorization": token})
        if res.status_code != 200:
            return "The system was utterly unable to safely retrieve the required document information"
        
        doc = res.json().get("data", {})
        if not doc.get("content"):
            return "The specified document contains absolutely no textual content required for translation"
            
        text = doc["content"]
        if doc.get("content_format") == "json":
            try:
                text = "\n\n".join([b.get("data", {}).get("text", "") for b in json.loads(text).get("blocks", []) if b.get("data", {}).get("text", "")])
            except Exception: pass
            
        trans_res = await _make_api_request("POST", f"{INTERNAL_API_URL}/inference/translate", headers={"Authorization": token}, json={"text": text, "target_lang": target_language}, timeout=60)
        if trans_res.status_code != 200 or not trans_res.json().get("translation"):
            return "The artificial intelligence linguistic translation service encountered an unexpected execution failure"
            
        translated = trans_res.json()["translation"]
        if doc.get("content_format") == "json":
            translated = json.dumps({"blocks": [{"type": "paragraph", "data": {"text": p.strip()}} for p in translated.split("\n\n") if p.strip()] + [{"type": "paragraph", "data": {"text": "<i>Content generated by DocLib AI</i>"}}]})
            
        slug = re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", unicodedata.normalize("NFKD", f"[Translation {target_language}] {doc.get('title')}").encode("ascii", "ignore").decode("ascii")).strip().lower())
        create_res = await _make_api_request("POST", f"{INTERNAL_API_URL}/documents/", headers={"Authorization": token}, json={"title": f"[Translation {target_language}] {doc.get('title')}", "slug": f"{slug}-{int(datetime.datetime.now().timestamp())}", "description": f"Translation to {target_language}", "visibility": "private", "content_format": doc.get("content_format", "json"), "content": translated, "status": "draft"})
        
        if create_res.status_code in [200, 201]:
            new_id = create_res.json().get("data", {}).get("id") or create_res.json().get("data", {}).get("_id")
            if new_id:
                return f"The linguistic translation was generated and safely archived successfully [View translation](/editor?document_id={new_id})"
            return "The linguistic translation generated successfully however the system failed retrieving identifier"
        return "The translation generated correctly but the system encountered error saving documentation"
    except Exception:
        logger.error("The system encountered a massive failure establishing translation structural communication pipes")
        return "The system encountered an unexpected error and requires you to try again later"

tools = [
    agent_summarize_long_document, get_user_balance, get_transaction_history, redeem_voucher,
    get_revenue_report, get_my_documents, read_document, get_trash_documents, delete_document,
    restore_document, get_document_analytics, agent_suggest_citations, agent_peer_review,
    agent_transform_tone, create_document, update_document, create_deposit_link, translate_document
]

_hf_endpoint = HuggingFaceEndpoint(task="conversational", repo_id=settings.LLAMA_MODEL, huggingfacehub_api_token=settings.HF_TOKEN, temperature=0.1)
llm = ChatHuggingFace(llm=_hf_endpoint)