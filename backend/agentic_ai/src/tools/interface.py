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
                from src.store.database import vector_store

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

from src.api.inference import peer_review, suggest_citations, transform_tone

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
        data = await suggest_citations(req)
        return f"Here are the suggested citations for the document:\n\n{data.get('citations', '')}"
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
        data = await peer_review(req)
        return f"Here is the peer review report for the document:\n\n{data.get('review_report', '')}"
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
        data = await transform_tone(req)
        return f"Here is the text transformed to the requested tone:\n\n{data.get('transformed_text', '')}"
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
            f"{INTERNAL_API_URL}/tai-lieu/",
            headers=headers,
            json=create_payload,
        )
        if res_create.status_code in [200, 201]:
            new_doc = res_create.json().get("data", {})
            doc_id = new_doc.get("id") or new_doc.get("_id")
            if doc_id:
                return f"New document created successfully. [View Document](/editor?document_id={doc_id})"
            return "The document was successfully initialized but its identifier could not be retrieved"
        return "An issue occurred while creating and storing the new document"
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
        return "No content changes were recorded for this document"

    try:
        res_update = await _make_api_request(
            "PUT",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers=headers,
            json=payload,
        )
        if res_update.status_code in [200, 201]:
            return f"Document updated successfully. [View Document](/editor?document_id={document_id})"
        raise Exception("Error updating document")
    except Exception as e:
        raise Exception(f"An abnormal error occurred during data flow processing {e}")

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
