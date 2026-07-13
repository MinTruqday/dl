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
    """
    Get the current user's DocLib wallet balance in dl currency.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks about their remaining credits, balance, or how much money they have.

    CRITICAL: Requires authentication. If unauthorized, prompt the user to log in.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "High security operation, please log in to your account and try again"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/vi-tien/so-du",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            balance = data.get("balance", 0)
            return f"Your current account balance is {balance} credits"
        elif response.status_code == 401:
            return "Your session has expired. Please log in again"
        raise Exception("Failed to load account balance")
    except Exception as e:
        logger.exception("Failed to access balance data")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def get_transaction_history(config: RunnableConfig) -> str:
    """
    View recent financial transaction history including deposit and payments.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks for a history of their deposits, top-ups, payments, or where their money went.

    CRITICAL: Only shows recent transactions. Requires authentication.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Please authenticate your account to view transaction history details"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/vi-tien/giao-dich",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "No recent payment transactions recorded"
            history_text = ""
            for i, tx in enumerate(data[:5]):
                tx_type = "Deposit" if tx.get("type") == "TOPUP" else "Payment"
                amount = tx.get("amount", 0)
                note = tx.get("note", "No content")
                history_text += f"{i+1} {tx_type} transaction of {amount} credits with note {note}\n"
            return f"Here is your recent transaction history:\n{history_text}"
        return "System is experiencing issues retrieving your payment transaction history"
    except Exception as e:
        logger.exception("Failed to retrieve payment transaction history")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def redeem_voucher(code: str, config: RunnableConfig) -> str:
    """
    Redeem a gift voucher code to add funds to the account.

    WHEN TO USE THIS TOOL:
    - Use this when the user explicitly provides a voucher code or promo code and asks to redeem it.

    CRITICAL: The code must be a non-empty string.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Valid account login is required to use a gift voucher"
    if not code or not code.strip():
        return "This promo code is invalid or has already been used"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "POST",
            json={"code": code.strip()},
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            res_data = response.json().get("data", {})
            bonus = res_data.get("bonus_dl", 0)
            return f"Gift voucher redeemed successfully. Your account has been credited with {bonus} credits"
        return "The system cannot process the gift voucher redemption request at this time"
    except Exception as e:
        logger.exception("Failed to process reward redemption request")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def get_revenue_report(config: RunnableConfig) -> str:
    """
    View revenue report from document sales, intended for authors.

    WHEN TO USE THIS TOOL:
    - Use this when a document author asks about their earnings, total revenue, or pending withdrawals.

    CRITICAL: This report is for document authors only. Requires authentication. Returns aggregated revenue and pending withdrawal amounts.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "For security reasons, please log in before viewing the revenue report"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/rut-tien/doanh-thu",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            total = data.get("total_revenue", 0)
            pending = data.get("pending_withdrawal", 0)
            return f"Financial report shows total revenue of {total} currency units with {pending} units pending withdrawal"
        return "Unable to retrieve financial revenue statistics"
    except Exception as e:
        logger.exception("Failed to load revenue report")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def get_my_documents(config: RunnableConfig) -> str:
    """
    List all personal documents owned or published by the current user.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks to see their documents, what they have written, or their library.

    CRITICAL: Returns an empty-library message if no documents exist. Requires authentication.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Please log into the system to browse your document library"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/ca-nhan",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "Your personal library currently does not have any documents"
            res = "Here is the list of your available documents\n"
            for doc in data:
                res += f"Document {doc.get('title')} is currently in {doc.get('status')} status\n"
            return res
        return "Encountered difficulties loading the document list from the database"
    except Exception as e:
        logger.exception("Failed to load document list from MongoDB")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def get_trash_documents(config: RunnableConfig) -> str:
    """
    View deleted documents currently in the trash bin.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks about deleted files, trash bin, or recovering a deleted document.

    CRITICAL: Requires authentication. Only shows files deleted by this user.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "You need to authenticate your identity to continue"
    if not _check_system_access(token):
        return "Security warning: You do not have sufficient privileges to access this area"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/thung-rac",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data:
                return "There are no documents in your trash bin"
            res = "The following documents are located within the trash bin\n"
            for doc in data:
                res += f"Document {doc.get('title')} was deleted on {doc.get('deleted_at')}\n"
            return res
        return "Connection to trash bin data is currently experiencing issues"
    except Exception as e:
        logger.exception("Failed to load deleted items list")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def delete_document(document_id: str, config: RunnableConfig) -> str:
    """
    Delete a document by ID, moving it to the trash bin.

    WHEN TO USE THIS TOOL:
    - Use this when the user explicitly requests to delete, remove, or trash a specific document.

    CRITICAL: Requires the exact document ID.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "The system requires you to log in to confirm ownership before deleting a document"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "DELETE",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            try:
                from src.store.vector import vector_store

                await vector_store.delete_by_document(document_id)
                logger.info("Document index cleanup completed successfully")
            except Exception as e:
                logger.exception("Failed to clean up document index")
            return "The document has been completely removed from the system"
        return "Document deletion failed due to a system error"
    except Exception as e:
        logger.exception("Document deletion failed due to system error")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def restore_document(document_id: str, config: RunnableConfig) -> str:
    """
    Restore a document from the trash bin by its ID.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks to recover, undelete, or restore a previously deleted document.

    CRITICAL: Requires the exact document ID of a deleted document.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "You need to authenticate your identity to continue"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/khoi-phuc",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            return "Your document has been successfully restored to its original state"
        return "Document restoration from the trash bin failed"
    except Exception as e:
        logger.exception("Document restoration from trash failed")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def get_document_analytics(document_id: str, config: RunnableConfig) -> str:
    """
    View detailed analytics including read count and drop-off rate for a document.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks how well their document is performing, how many reads it has, or its drop-off rate.

    CRITICAL: Requires the exact document ID.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "You need to authenticate your identity to continue"
    if not _check_system_access(token):
        return "You do not have sufficient privileges to perform this operation"

    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/phan-tich/bo-do",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            readers = data.get("readers_started", 0)
            rate = data.get("dropoff_rate", 0)
            return f"Reader analytics show {readers} readers with a bounce rate of {rate}%"
        return "Error aggregating and exporting statistical report data"
    except Exception as e:
        logger.exception("Failed to retrieve analytics data")
        raise Exception(f"An unexpected error occurred, please try again {e}")

async def _get_doc_text(document_id: str, token: str) -> str:
    try:
        res = await _make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers={"Authorization": token},
            timeout=30.0,
        )
        if res.status_code == 200:
            return res.json().get("data", {}).get("content", "")
    except Exception as e:
        logger.exception("Failed to load document content")
    return ""
from src.schemas.inference import CitationRequest, ReviewRequest, ToneRequest

@tool
async def agent_suggest_citations(document_id: str, config: RunnableConfig) -> str:
    """
    Suggest academic citations for a document by its ID.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks to generate, find, or suggest citations (APA, MLA, etc.) for a specific document.

    CRITICAL: Requires the exact document ID. Only works if the document has readable text.
    """
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "The actual content of the document is currently unavailable"
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512 * 2, chunk_overlap=0
    )
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = CitationRequest(text=safe_text, style="APA")
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/suy-luan/trich-dan-thong-minh",
            headers={"Authorization": token},
            json=req.model_dump(),
            timeout=180.0
        )
        if response.status_code == 200:
            data = response.json()
            return f"Here are the suggested citations for the document:\n\n{data.get('citations', '')}"
        return "Failed to generate citation suggestions from the inference service."
    except Exception as e:
        logger.exception("Failed to generate citation suggestions")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def agent_peer_review(document_id: str, config: RunnableConfig) -> str:
    """
    Perform an automated AI peer review of a document, evaluating strengths, weaknesses, and academic quality.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks for feedback, critique, peer review, or an evaluation of their document.

    CRITICAL: Requires the exact document ID. Provides a detailed critique report.
    """
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "The actual content of the document is currently unavailable"
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512 * 4, chunk_overlap=0
    )
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ReviewRequest(text=safe_text)
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/suy-luan/kiem-duyet-noi-dung",
            headers={"Authorization": token},
            json=req.model_dump(),
            timeout=180.0
        )
        if response.status_code == 200:
            data = response.json()
            return f"Here is the peer review report for the document:\n\n{data.get('review_report', '')}"
        return "Failed to generate peer review report from the inference service."
    except Exception as e:
        logger.exception("Peer review process failed")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def agent_transform_tone(
    document_id: str, tone: str, config: RunnableConfig
) -> str:
    """
    Transform the writing tone of a document (e.g., to academic, professional, casual, enthusiastic).

    WHEN TO USE THIS TOOL:
    - Use this when the user asks to rewrite, rephrase, or change the tone/style of a document.

    CRITICAL: Requires the exact document ID and a specific 'tone' string (e.g., 'academic'). Returns the transformed text.
    """
    token = config.get("configurable", {}).get("token")
    text = await _get_doc_text(document_id, token)
    if not text:
        return "The actual content of the document is currently unavailable"
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512 * 2, chunk_overlap=0
    )
    safe_text = splitter.split_text(text)[0] if text else ""
    try:
        req = ToneRequest(text=safe_text, tone=tone, expansion=False)
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/suy-luan/bien-doi-van-ban",
            headers={"Authorization": token},
            json=req.model_dump(),
            timeout=180.0
        )
        if response.status_code == 200:
            data = response.json()
            return f"Here is the text transformed to the requested tone:\n\n{data.get('transformed_text', '')}"
        return "Failed to transform tone using the inference service."
    except Exception as e:
        logger.exception("Tone transformation failed")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def create_deposit_link(amount: int, config: RunnableConfig) -> str:
    """
    Create a deposit link to top up the user's dl wallet. Returns a payment URL.

    WHEN TO USE THIS TOOL:
    - Use this when the user explicitly asks to top up, deposit money, or add funds to their account.

    CRITICAL: Requires an integer amount in VND. Requires user authentication.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "You need to authenticate your account before proceeding with a deposit"
    headers = {"Authorization": token}
    try:
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/nap-tien",
            json={"amount": amount},
            headers=headers,
            timeout=30.0,
        )
        if response.status_code in [200, 201]:
            data = response.json().get("data", {})
            checkout_url = data.get("checkout_url") or data.get("payment_url")
            if checkout_url:
                return f"A deposit request for {amount} currency units has been created. Please visit the following link to proceed with the payment: [Pay here]({checkout_url}/)"
            return "The system cannot generate a secure payment link at this time"
        return "A critical error occurred while starting the payment transaction process"
    except Exception as e:
        logger.exception("Failed to process deposit request")
        raise Exception(f"An unexpected error occurred, please try again {e}")

from src.workflow.reduction import agent_summarize_long_document

@tool
async def create_document(
    title: str, description: str, content: str, format: str, config: RunnableConfig
) -> str:
    """
    Create a new document in the user's library.

    WHEN TO USE THIS TOOL:
    - Use this tool ONLY when the user explicitly asks to create, write, or generate a new file, report, blog, or long-form content. Do NOT use this for short conversational responses (<= 20 lines) or quick lists.

    CRITICAL: - format MUST be either 'json' (for EditorJS) or 'latex' (for Math/Science).
    - If format is 'latex', content MUST include standard LaTeX boilerplate (\\documentclass, \\begin{document}).
    - If format is 'json', content MUST be a valid EditorJS JSON string with a 'blocks' array. Example: {"blocks": [{"type": "paragraph", "data": {"text": "Hello"}}]}
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "You need to authenticate your identity to continue"

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
            timeout=10.0,
        )
        if res_profile.status_code == 200:
            profile_data = res_profile.json().get("data", {})
            user_name = (
                profile_data.get("full_name") or profile_data.get("name") or "User"
            )
    except Exception as e:
        logger.exception("Failed to load user profile for author information")

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
            f"{INTERNAL_API_URL}/tai-lieu",
            headers=headers,
            json=create_payload,
        )
        if res_create.status_code in [200, 201]:
            new_doc = res_create.json().get("data", {})
            doc_id = new_doc.get("id") or new_doc.get("_id")
            if doc_id:
                return f"New document created successfully. [View Document](/editor?document_id={doc_id})"
            return "The document was successfully initialized but its identifier could not be retrieved"
        return f"An issue occurred while creating and storing the new document: Status {res_create.status_code} - {res_create.text}"
    except Exception as e:
        raise Exception(f"An abnormal error occurred during data flow processing {e}")

@tool
async def read_document(document_id: str, config: RunnableConfig) -> str:
    """
    Read the content of a document by its ID.

    WHEN TO USE THIS TOOL:
    - Use this when you need to know the current content of a document before modifying it, or when the user asks you to read or summarize a specific document by its ID.

    CRITICAL: Requires the exact document ID. Returns the raw content format.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "You need to authenticate your identity to continue"

    headers = {"Authorization": token}
    try:
        res = await _make_api_request(
            "GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers
        )
        if res.status_code != 200:
            return "Cannot extract detailed information data of the document"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    format = doc_data.get("content_format", "json")
    content = doc_data.get("content", "")

    if format == "json":
        return f"The document uses the standard format with the following content:\n{content}"
    elif format == "latex":
        return f"The document uses the mathematical format with the following content:\n{content}"
    else:
        return f"The document uses an alternative format with the following content:\n{content}"

@tool
async def update_document(
    document_id: str,
    new_content: str = None,
    title: str = None,
    description: str = None,
    config: RunnableConfig = None,
) -> str:
    """
    Update an existing document's content, title, or description by its ID.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks to edit, modify, append, or change an existing document. ALWAYS read the document first using read_document before calling this to ensure you don't accidentally erase existing content.

    CRITICAL: Only provide the fields you want to update.
    - If format is 'json', new_content MUST be a valid EditorJS JSON string (with "blocks" array).
    - If format is 'latex', new_content MUST be the full LaTeX source code.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "You need to authenticate your identity to continue"

    headers = {"Authorization": token}

    try:
        res = await _make_api_request(
            "GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers
        )
        if res.status_code != 200:
            return "Operation not permitted: Due to security restrictions or the document no longer exists"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    meta_payload = {}
    if title:
        meta_payload["title"] = title
    if description:
        meta_payload["description"] = description

    if meta_payload:
        try:
            res_meta = await _make_api_request(
                "PUT",
                f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
                headers=headers,
                json=meta_payload,
            )
            if res_meta.status_code not in [200, 201]:
                return f"Error updating document metadata. API returned {res_meta.status_code}"
        except Exception as e:
            raise Exception(f"Error during metadata update {e}")

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
            
        content_payload = {
            "content": final_content,
            "content_format": format
        }
        
        try:
            res_content = await _make_api_request(
                "PUT",
                f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung",
                headers=headers,
                json=content_payload,
            )
            if res_content.status_code not in [200, 201]:
                return f"Error updating document content. API returned {res_content.status_code}"
        except Exception as e:
            raise Exception(f"Error during content update {e}")

    if not meta_payload and not new_content:
        return "No content changes were recorded for this document"

    return f"Document updated successfully. [View Document](/editor?document_id={document_id})"

@tool
async def translate_document(
    document_id: str, target_language: str, config: RunnableConfig
) -> str:
    """
    Translate an existing document to a target language. This operation creates a new translated document rather than overwriting the original.

    WHEN TO USE THIS TOOL:
    - Use this when the user asks to translate, convert language, or localize a specific document.

    CRITICAL: If language is not specified, default to English. Requires the exact document ID.
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return "You need to authenticate your identity to continue"

    headers = {"Authorization": token}

    try:
        res = await _make_api_request(
            "GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers
        )
        if res.status_code != 200:
            return "Cannot extract detailed information data of the document"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    original_content = doc_data.get("content", "")
    format = doc_data.get("content_format", "json")
    original_title = doc_data.get("title", "Document")

    if not original_content:
        return "This document is completely empty or does not contain valid text content to perform translation"

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
            return "The language translation service is currently experiencing connection issues"
        translated_text = trans_res.json().get("translation", "")
    except Exception:
        return "The entire document translation cycle was cancelled due to an error"

    if not translated_text:
        return "The document content translation process encountered an unknown error"

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
                "data": {"text": "<i>Content generated by DocLib Metis</i>"},
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
                "\\vspace{1em}\n\\noindent\\textit{Content generated by DocLib Metis}\n\\end{document}",
            )
        else:
            new_content = (
                translated_text
                + "\n\n\\vspace{1em}\n\\noindent\\textit{Content generated by DocLib Metis}"
            )
    else:
        new_content = translated_text + "\n\n(Content generated by DocLib Metis)"

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
                return f"Translation created and saved successfully, you can view it here. [View Translation](/editor?document_id={new_doc_id})"
            return "Translation is complete but could not be linked with a file identifier"
        return "Translation process completed but encountered an issue saving the result to the server"
    except Exception as e:
        logger.exception("Failed to create translated document")
        raise Exception(f"An unexpected error occurred, please try again {e}")

@tool
async def inspect_ui_components(query: str, config: RunnableConfig) -> str:
    """
    Dynamically search and read the source code of custom EditorJS blocks from the project's frontend.

    WHEN TO USE THIS TOOL:
    - Use this BEFORE calling create_document or update_document whenever you need to generate content for a specific custom block type (e.g., 'Chart', 'Kanban', 'Mermaid', 'Table'). Query for the component name to retrieve its TypeScript source and infer the exact JSON schema.

    CRITICAL: Calling this tool is a required first step before creating any document with custom UI blocks. Do NOT guess the JSON schema — read the source to confirm the exact structure.
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
            return f"No custom UI components found matching '{query}'. Try a different keyword"
        return "\n\n".join(results)
    except Exception as e:
        return f"Cannot initialize and export the new translated document file {e}"

@tool
async def agent_draft_with_memory(prompt: str, config: RunnableConfig) -> str:
    """
    Draft a document using the user's stored memory/preferences (communication style, tone preferences, role) to make the draft highly personalized.
    
    WHEN TO USE THIS TOOL:
    - Use this when the user asks to draft, write, or create a document based on a short prompt, and implies they want it tailored to their style or memory.
    """
    token = config.get("configurable", {}).get("token")
    try:
        from src.schemas.inference import DraftWithMemoryRequest
        req = DraftWithMemoryRequest(prompt=prompt)
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/suy-luan/nhap-van-ban-voi-ky-uc",
            headers={"Authorization": token},
            json=req.model_dump(),
            timeout=180.0
        )
        if response.status_code == 200:
            data = response.json()
            return f"Here is the personalized draft:\n\n{data.get('draft', '')}"
        return f"Failed to generate draft: {response.status_code} - {response.text}"
    except Exception as e:
        logger.exception("Failed to draft with memory")
        raise Exception(f"An unexpected error occurred {e}")

@tool
async def agent_extract_to_artifacts(document_id: str, extraction_goals: list[str], config: RunnableConfig) -> str:
    """
    Extract structured data (like Action Items, Leaderboards, Timelines) from a complex document and save it to the persistent Artifacts Storage.
    
    WHEN TO USE THIS TOOL:
    - Use this when the user wants to extract specific structured info from a document and save it persistently.
    """
    token = config.get("configurable", {}).get("token")
    try:
        from src.schemas.inference import ExtractToStorageRequest
        text = await _get_doc_text(document_id, token)
        if not text:
            return "The actual content of the document is currently unavailable"
        req = ExtractToStorageRequest(text=text, extraction_goals=extraction_goals)
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/suy-luan/trich-xuat-luu-tru",
            headers={"Authorization": token},
            json=req.model_dump(),
            timeout=180.0
        )
        if response.status_code == 200:
            data = response.json()
            return f"Data successfully extracted and stored in artifacts:\n\n{data.get('summary', '')}"
        return f"Failed to extract to storage: {response.status_code} - {response.text}"
    except Exception as e:
        logger.exception("Failed to extract to storage")
        raise Exception(f"An unexpected error occurred {e}")

@tool
async def agent_web_fact_check(document_id: str, config: RunnableConfig) -> str:
    """
    Fact-check the claims in a document using Web Search to verify facts, especially those occurring after January 2026.
    
    WHEN TO USE THIS TOOL:
    - Use this to verify or fact-check a document against recent real-world events.
    """
    token = config.get("configurable", {}).get("token")
    try:
        from src.schemas.inference import WebFactCheckRequest
        text = await _get_doc_text(document_id, token)
        if not text:
            return "The actual content of the document is currently unavailable"
        req = WebFactCheckRequest(text=text)
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/suy-luan/kiem-chung-su-that",
            headers={"Authorization": token},
            json=req.model_dump(),
            timeout=180.0
        )
        if response.status_code == 200:
            data = response.json()
            return f"Fact-checking results:\n\n{data.get('fact_check_report', '')}"
        return f"Failed to fact check: {response.status_code} - {response.text}"
    except Exception as e:
        logger.exception("Failed to fact check")
        raise Exception(f"An unexpected error occurred {e}")

@tool
async def agent_compliance_screener(document_id: str, config: RunnableConfig) -> str:
    """
    Scan a document for compliance, checking for child-safety risks, grooming, and financial/legal advice disclaimers.
    
    WHEN TO USE THIS TOOL:
    - Use this when the user asks to review a document for safety, compliance, legal risks, or appropriate tone before publishing.
    """
    token = config.get("configurable", {}).get("token")
    try:
        from src.schemas.inference import ComplianceScreenRequest
        text = await _get_doc_text(document_id, token)
        if not text:
            return "The actual content of the document is currently unavailable"
        req = ComplianceScreenRequest(text=text)
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/suy-luan/kiem-duyet-an-toan",
            headers={"Authorization": token},
            json=req.model_dump(),
            timeout=180.0
        )
        if response.status_code == 200:
            data = response.json()
            return f"Compliance screening results:\n\n{data.get('compliance_report', '')}"
        return f"Failed to screen document: {response.status_code} - {response.text}"
    except Exception as e:
        logger.exception("Failed to screen document")
        raise Exception(f"An unexpected error occurred {e}")

@tool
async def agent_semantic_diff(document_id_1: str, document_id_2: str, config: RunnableConfig) -> str:
    """
    Perform a semantic comparison between two documents to explain how viewpoints, arguments, or clauses have changed conceptually.
    
    WHEN TO USE THIS TOOL:
    - Use this when the user wants to understand the meaning or conceptual difference between two documents or versions.
    """
    token = config.get("configurable", {}).get("token")
    try:
        from src.schemas.inference import SemanticDiffRequest
        text1 = await _get_doc_text(document_id_1, token)
        text2 = await _get_doc_text(document_id_2, token)
        if not text1 or not text2:
            return "The actual content of the documents is currently unavailable"
        req = SemanticDiffRequest(text1=text1, text2=text2)
        response = await _make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/suy-luan/so-sanh-ngu-nghia",
            headers={"Authorization": token},
            json=req.model_dump(),
            timeout=180.0
        )
        if response.status_code == 200:
            data = response.json()
            return f"Semantic differences:\n\n{data.get('diff_report', '')}"
        return f"Failed to compare documents: {response.status_code} - {response.text}"
    except Exception as e:
        logger.exception("Failed to compare documents")
        raise Exception(f"An unexpected error occurred {e}")

@tool
async def conversation_search(query: str, config: RunnableConfig) -> str:
    """
    Search past conversations by topic keywords.
    
    WHEN TO USE THIS TOOL:
    - When the user references a specific past conversation by topic, project name, or keyword (e.g., "the bug we discussed", "my project").
    - Use content nouns (the topic, the proper noun, the project name), not meta-words like "discussed" or "yesterday". Keep it to a few distinctive terms.
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Lỗi hệ thống: Cần có định danh người dùng để tìm kiếm cuộc trò chuyện"
    try:
        from src.services.history import HistoryService
        sessions = await HistoryService.search_by_keyword(user_id, query)
        if not sessions:
            return "Không tìm thấy cuộc trò chuyện nào phù hợp"
        
        result = "Hệ thống đã tìm thấy các cuộc trò chuyện liên quan sau:\\n"
        for s in sessions:
            title = s.get("title", "Không có tiêu đề")
            updated = s.get("updated_at", "")
            result += f"- {title} (Cập nhật lần cuối: {updated})\\n"
        return result
    except Exception as e:
        logger.exception("Failed to search conversations")
        return f"Lỗi hệ thống khi tìm kiếm cuộc trò chuyện: {str(e)}"

@tool
async def recent_chats(days: int, config: RunnableConfig) -> str:
    """
    Find past conversations by time window.
    
    WHEN TO USE THIS TOOL:
    - When the anchor is temporal (e.g., "yesterday," "last week," "my first chats").
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Lỗi hệ thống: Cần có định danh người dùng để lấy lịch sử trò chuyện"
    try:
        from src.services.history import HistoryService
        sessions = await HistoryService.get_recent_chats(user_id, days)
        if not sessions:
            return "Không tìm thấy cuộc trò chuyện nào trong khoảng thời gian này"
        
        result = f"Hệ thống đã tìm thấy các cuộc trò chuyện gần đây (trong {days} ngày qua):\\n"
        for s in sessions:
            title = s.get("title", "Không có tiêu đề")
            updated = s.get("updated_at", "")
            result += f"- {title} (Cập nhật lần cuối: {updated})\\n"
        return result
    except Exception as e:
        logger.exception("Failed to fetch recent conversations")
        return f"Lỗi hệ thống khi truy xuất lịch sử trò chuyện: {str(e)}"

@tool
async def memory_user_edits(action: str, content: str, config: RunnableConfig, memory_id: str = None) -> str:
    """
    Manage user edits to memory (e.g., "remember this", "forget that").
    
    WHEN TO USE THIS TOOL:
    - If a person asks you to remember or forget something, you MUST use memory_user_edits.
    - ALWAYS use the tool BEFORE confirming any memory action. DO NOT just acknowledge conversationally.
    
    Args:
        action (str): The action to perform. Valid options: 'add', 'update', 'delete'.
        content (str): The content to remember or update.
        memory_id (str, optional): The ID of the memory to update or delete.
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Lỗi hệ thống: Cần có định danh người dùng để quản lý trí nhớ"
    try:
        from src.memory.mem0 import mem0_manager
        if action == "add":
            await mem0_manager.add_memory([{"role": "user", "content": content}], user_id=user_id)
            return "Hệ thống đã ghi nhớ thông tin thành công"
        elif action == "update" and memory_id:
            await mem0_manager.update_memory(memory_id=memory_id, new_content=content)
            return "Hệ thống đã cập nhật trí nhớ thành công"
        elif action == "delete" and memory_id:
            await mem0_manager.delete_memory(memory_id=memory_id)
            return "Hệ thống đã xóa trí nhớ thành công"
        else:
            return "Yêu cầu không hợp lệ hoặc thiếu mã định danh trí nhớ"
    except Exception as e:
        logger.exception("Failed to edit memory")
        return f"Lỗi hệ thống khi xử lý trí nhớ: {str(e)}"

@tool
async def visualizer(code: str, type: str, config: RunnableConfig) -> str:
    """
    Stream inline SVG diagrams, illustrations, and HTML interactive widgets into the conversation.
    
    WHEN TO USE THIS TOOL:
    - Use when a visual genuinely aids understanding more than text alone (e.g., spatial relationships, data shape, system structure, process flow).
    - Triggered by phrases like: "show me," "visualize," "diagram," "chart," "illustrate," "draw," "graph."
    - DO NOT use this tool if the user wants to create a file or save to disk.
    
    Args:
        code (str): The raw SVG or HTML code to render.
        type (str): The type of code ('svg' or 'html').
    """
    return "Hình ảnh trực quan đã được hiển thị thành công cho người dùng"

@tool
async def search_mcp_registry(query: str, config: RunnableConfig) -> str:
    """
    Search the MCP registry for available third-party apps and connectors.
    
    WHEN TO USE THIS TOOL:
    - When the user asks to connect to an external app (e.g., "connect my calendar", "find a hike on HikeService").
    - Use this BEFORE calling suggest_connectors to find the relevant directoryUuid.
    """
    try:
        from src.services.mcp import MCPService
        import json
        results = await MCPService.search_registry(query)
        if not results:
            return "Hệ thống không tìm thấy ứng dụng bên thứ ba nào phù hợp"
        return f"Hệ thống đã tìm thấy các ứng dụng sau:\\n{json.dumps(results, indent=2)}"
    except Exception as e:
        logger.exception("Failed to search MCP registry")
        return f"Lỗi hệ thống khi tìm kiếm danh mục ứng dụng: {str(e)}"

@tool
async def suggest_connectors(uuids: list[str], config: RunnableConfig) -> str:
    """
    Suggest MCP connectors for the user to authorize/connect.
    
    WHEN TO USE THIS TOOL:
    - After searching the registry and finding a relevant but unconnected app, use this to prompt the user to connect it.
    - NEVER call an unconnected [third_party_mcp_app] directly without suggesting it first.
    """
    try:
        from src.services.mcp import MCPService
        import json
        result = await MCPService.suggest_connector(uuids)
        return f"Hệ thống đã gửi đề xuất kết nối cho người dùng:\\n{json.dumps(result, indent=2)}"
    except Exception as e:
        logger.exception("Failed to suggest connectors")
        return f"Lỗi hệ thống khi đề xuất kết nối: {str(e)}"

@tool
async def execute_mcp_tool(directory_uuid: str, tool_name: str, arguments: dict, config: RunnableConfig) -> str:
    """
    Execute a tool provided by a connected third-party MCP app.
    
    WHEN TO USE THIS TOOL:
    - Only after verifying the app is connected.
    - Pass the correct directory_uuid of the MCP server, the target tool_name, and required arguments as a dictionary.
    """
    try:
        from src.services.mcp import MCPService
        result = await MCPService.execute_tool(directory_uuid, tool_name, arguments)
        
        # result is an mcp.types.CallToolResult. Let's serialize it.
        # In the MCP SDK, CallToolResult has 'content' (list of text/image) and 'isError'.
        text_content = ""
        for c in result.content:
            if c.type == "text":
                text_content += c.text + "\\n"
        
        status = "Thất bại" if result.isError else "Thành công"
        return f"Kết quả thực thi công cụ '{tool_name}' trên MCP Server ({status}):\\n{text_content}"
    except Exception as e:
        logger.exception("Failed to execute MCP tool")
        return f"Lỗi hệ thống khi thực thi công cụ MCP: {str(e)}"

@tool
async def find_location(config: RunnableConfig) -> str:
    """
    Find the user's current location and timezone.
    
    WHEN TO USE THIS TOOL:
    - When the user asks location/time queries (e.g., "what's the weather like here?", "what time is it for me?").
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://ip-api.com/json/")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return (
                        f"Vị trí hiện tại: {data.get('city')}, {data.get('regionName')}, {data.get('country')}\\n"
                        f"Múi giờ: {data.get('timezone')}\\n"
                        f"Tọa độ: {data.get('lat')}, {data.get('lon')}"
                    )
        return "Hệ thống không thể xác định vị trí hiện tại"
    except Exception as e:
        logger.exception("Failed to find location")
        return f"Lỗi hệ thống khi xác định vị trí: {str(e)}"

@tool
async def web_search(query: str, config: RunnableConfig) -> str:
    """
    Search for current information on the web.

    WHEN TO USE THIS TOOL:
    - Finding recent events or news.
    - Looking up current information beyond the AI's knowledge cutoff.
    - Researching topics that require up-to-date data.
    - Fact-checking or verifying information.
    """
    from src.agents.engine import search_engine
    try:
        result = await search_engine.execute(query)
        return result
    except Exception as e:
        logger.exception("Web search execution failed")
        return f"Hệ thống không thể thực hiện tìm kiếm web vào lúc này: {str(e)}"

@tool
async def image_search(query: str, config: RunnableConfig) -> str:
    """
    Search and find images on the web, returning them along with their dimensions.

    WHEN TO USE THIS TOOL:
    - When the user asks to see what something looks like, or asks for visual references.
    
    CRITICAL: Keep queries specific (3-6 words).
    """
    from src.agents.engine import search_engine
    try:
        result = await search_engine.image_search(query)
        return result
    except Exception as e:
        logger.exception("Image search execution failed")
        return f"Hệ thống không thể tìm kiếm hình ảnh vào lúc này: {str(e)}"

from src.tools.surgical_editing import (
    read_document_section,
    edit_document_text,
    edit_document_block,
    propose_document_edits
)

from src.tools.search import glob_search, grep_search

tools = [
    glob_search,
    grep_search,
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
    agent_draft_with_memory,
    agent_extract_to_artifacts,
    agent_web_fact_check,
    agent_compliance_screener,
    agent_semantic_diff,
    conversation_search,
    recent_chats,
    memory_user_edits,
    visualizer,
    search_mcp_registry,
    suggest_connectors,
    execute_mcp_tool,
    find_location,
    web_search,
    image_search,
    read_document_section,
    edit_document_text,
    edit_document_block,
    propose_document_edits,
]

llama_model = settings.LLM_MODEL
hf_token = settings.HF_TOKEN

_hf_endpoint = HuggingFaceEndpoint(
    task="conversational",
    repo_id=llama_model,
    huggingfacehub_api_token=hf_token,
    temperature=0.1,
)

llm = ChatHuggingFace(llm=_hf_endpoint)
