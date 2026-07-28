import json
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger
from src.tools.http_client import INTERNAL_API_URL, check_system_access, make_api_request


async def _get_doc_text(document_id: str, token: str) -> str:
    try:
        res = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers={"Authorization": token},
            timeout=30.0,
        )
        if res.status_code == 200:
            return res.json().get("data", {}).get("content", "")
    except Exception:
        logger.exception("Failed to load document content")
    return ""


@tool
async def create_document(
    title: str,
    content_format: str = "doclib",
    content: str = "",
    description: str = "",
    config: RunnableConfig = None,
) -> str:
    """
    <module_purpose>
    Create a new EditorJS or LaTeX document owned by the authenticated user
    </module_purpose>
    <contract>
    Use doclib for EditorJS JSON and doclibx for LaTeX source
    EditorJS content must contain a blocks array
    Empty content creates a valid starter document for the selected format
    </contract>
    """
    token = (config or {}).get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    normalized_format = content_format.strip().lower()
    if normalized_format not in {"doclib", "doclibx"}:
        return json.dumps({"status": "unsupported_document_format"})
    normalized_content = content
    if normalized_format == "doclib":
        if not normalized_content.strip():
            normalized_content = json.dumps(
                {"time": 0, "blocks": [], "version": "2.30.8"}
            )
        try:
            parsed = json.loads(normalized_content)
        except (TypeError, json.JSONDecodeError):
            return json.dumps({"status": "document_content_invalid"})
        if not isinstance(parsed, dict) or not isinstance(parsed.get("blocks"), list):
            return json.dumps({"status": "document_content_invalid"})
        normalized_content = json.dumps(parsed, ensure_ascii=False)
    elif not normalized_content.strip():
        normalized_content = (
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\end{document}\n"
        )
    payload = {
        "title": title,
        "description": description,
        "content": normalized_content,
        "content_format": normalized_format,
        "visibility": "private",
    }
    try:
        response = await make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/tai-lieu",
            headers={"Authorization": token},
            json=payload,
            timeout=30.0,
        )
        if response.status_code != 201:
            return json.dumps(
                {
                    "status": "document_creation_failed",
                    "upstream_status": response.status_code,
                }
            )
        data = response.json().get("data", {})
        return json.dumps(
            {
                "status": "success",
                "document_id": data.get("_id") or data.get("id"),
                "content_format": normalized_format,
            }
        )
    except Exception:
        logger.exception("Document creation failed")
        return json.dumps({"status": "document_service_unavailable"})


@tool
async def update_document_metadata(
    document_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[list[str]] = None,
    config: RunnableConfig = None,
) -> str:
    """
    <module_purpose>
    Update editable metadata for one document without changing its content
    </module_purpose>
    <contract>
    Provide the exact document ID and at least one metadata field
    Existing content and format remain unchanged
    </contract>
    """
    token = (config or {}).get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    values = {
        "title": title,
        "description": description,
        "category": category,
        "tags": tags,
    }
    payload = {key: value for key, value in values.items() if value is not None}
    if not payload:
        return json.dumps({"status": "document_update_empty"})
    try:
        response = await make_api_request(
            "PUT",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers={"Authorization": token},
            json=payload,
            timeout=30.0,
        )
        if response.status_code != 200:
            return json.dumps(
                {
                    "status": "document_update_failed",
                    "upstream_status": response.status_code,
                }
            )
        return json.dumps({"status": "success", "document_id": document_id})
    except Exception:
        logger.exception("Document metadata update failed")
        return json.dumps({"status": "document_service_unavailable"})


@tool
async def replace_document_content(
    document_id: str,
    content: str,
    content_format: str,
    config: RunnableConfig = None,
) -> str:
    """
    <module_purpose>
    Replace the complete EditorJS or LaTeX source of an existing document
    </module_purpose>
    <contract>
    Use doclib for EditorJS JSON and doclibx for LaTeX source
    Prefer surgical edit tools when only a small region needs modification
    </contract>
    """
    token = (config or {}).get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    normalized_format = content_format.strip().lower()
    if normalized_format not in {"doclib", "doclibx"}:
        return json.dumps({"status": "unsupported_document_format"})
    normalized_content = content
    if normalized_format == "doclib":
        try:
            parsed = json.loads(content)
        except (TypeError, json.JSONDecodeError):
            return json.dumps({"status": "document_content_invalid"})
        if not isinstance(parsed, dict) or not isinstance(parsed.get("blocks"), list):
            return json.dumps({"status": "document_content_invalid"})
        normalized_content = json.dumps(parsed, ensure_ascii=False)
    elif not content.strip():
        return json.dumps({"status": "document_content_invalid"})
    try:
        response = await make_api_request(
            "PUT",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung",
            headers={"Authorization": token},
            json={
                "content": normalized_content,
                "content_format": normalized_format,
            },
            timeout=30.0,
        )
        if response.status_code != 200:
            return json.dumps(
                {
                    "status": "document_update_failed",
                    "upstream_status": response.status_code,
                }
            )
        from src.tools.editing import _broadcast_update

        await _broadcast_update(document_id, normalized_content)
        return json.dumps(
            {
                "status": "success",
                "document_id": document_id,
                "content_format": normalized_format,
            }
        )
    except Exception:
        logger.exception("Document content replacement failed")
        return json.dumps({"status": "document_service_unavailable"})


@tool
async def get_my_documents(config: RunnableConfig) -> str:
    """
    <module_purpose>
    List all personal documents owned or published by the current user.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks to see their documents, what they have written, or their library.
    CRITICAL: Returns an empty-library message if no documents exist. Requires authentication.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/ca-nhan",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            return json.dumps(
                {"status": "success", "documents": data},
                ensure_ascii=False,
            )
        return json.dumps({"status": "document_list_retrieval_failed"})
    except Exception:
        logger.exception("Failed to load document list from MongoDB")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def get_trash_documents(config: RunnableConfig) -> str:
    """
    <module_purpose>
    View deleted documents currently in the trash bin.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks about deleted files, trash bin, or recovering a deleted document.
    CRITICAL: Requires authentication. Only shows files deleted by this user.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    if not check_system_access(token):
        return json.dumps({"status": "insufficient_permissions"})

    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/thung-rac",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            return json.dumps(
                {"status": "success", "documents": data},
                ensure_ascii=False,
            )
        return json.dumps({"status": "trash_document_list_retrieval_failed"})
    except Exception:
        logger.exception("Failed to load deleted items list")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def delete_document(document_id: str, config: RunnableConfig) -> str:
    """
    <module_purpose>
    Delete a document by ID, moving it to the trash bin.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user explicitly requests to delete, remove, or trash a specific document.
    CRITICAL: Requires the exact document ID.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})

    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "DELETE",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            try:
                from src.store.vector import vector_store
                await vector_store.delete_by_document(document_id)
                logger.info("Document index cleanup completed")
            except Exception:
                logger.exception("Failed to clean up document index")
            return json.dumps({"status": "success", "document_id": document_id})
        return json.dumps({"status": "document_deletion_failed"})
    except Exception:
        logger.exception("Document deletion failed due to system error")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def restore_document(document_id: str, config: RunnableConfig) -> str:
    """
    <module_purpose>
    Restore a document from the trash bin by its ID.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks to recover, undelete, or restore a previously deleted document.
    CRITICAL: Requires the exact document ID of a deleted document.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})

    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/khoi-phuc",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            return json.dumps({"status": "success", "document_id": document_id})
        return json.dumps({"status": "document_restoration_failed"})
    except Exception:
        logger.exception("Document restoration from trash failed")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def get_document_analytics(document_id: str, config: RunnableConfig) -> str:
    """
    <module_purpose>
    View detailed analytics including read count and drop-off rate for a document.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks how well their document is performing, how many reads it has, or its drop-off rate.
    CRITICAL: Requires the exact document ID.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    if not check_system_access(token):
        return json.dumps({"status": "insufficient_permissions"})

    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/phan-tich/bo-do",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            readers = data.get("readers_started", 0)
            rate = data.get("dropoff_rate", 0)
            return json.dumps(
                {
                    "status": "success",
                    "readers_started": readers,
                    "dropoff_rate": rate,
                }
            )
        return json.dumps({"status": "document_analytics_retrieval_failed"})
    except Exception:
        logger.exception("Failed to retrieve analytics data")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def read_document(document_id: str, config: RunnableConfig) -> str:
    """
    <module_purpose>
    Read full text content of a document by document ID.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks to read, view, or analyze a specific document by its ID.
    CRITICAL: Requires a valid document_id.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    text = await _get_doc_text(document_id, token)
    if not text:
        return json.dumps({"status": "document_content_unavailable"})
    return text

@tool
async def recommend_documents(query: str, config: RunnableConfig) -> str:
    """
    <module_purpose>
    Search and recommend the top 3 most relevant documents for a project request or query.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks for document recommendations, reference materials, or templates for building a project.
    CRITICAL: Returns a structured summary of the top 3 matching documents including title, link, price, and match description.
    </contract>
    """
    import os
    from motor.motor_asyncio import AsyncIOMotorClient
    from src.core.infrastructure.database import database

    try:
        db_name = os.getenv("CONTENT_DB_NAME", "doclib_content")
        if database.mongodb:
            db = database.mongodb[db_name]
        else:
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://doclib_mongodb:27017")
            client = AsyncIOMotorClient(mongo_uri)
            db = client[db_name]

        search_filter = {
            "status": "published",
            "is_deleted": {"$ne": True},
        }
        if query and query.strip():
            search_filter["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}},
            ]

        docs = await db["documents"].find(search_filter).limit(3).to_list(length=3)

        if not docs:
            docs = await db["documents"].find({"status": "published", "is_deleted": {"$ne": True}}).limit(3).to_list(length=3)

        if not docs:
            return json.dumps({
                "status": "success",
                "query": query,
                "recommendations": [],
            }, ensure_ascii=False)

        recommendations = []
        for doc in docs:
            doc_id = str(doc.get("_id") or doc.get("id"))
            recommendations.append({
                "id": doc_id,
                "title": doc.get("title") or "",
                "slug": doc.get("slug", ""),
                "price_dl": doc.get("price_dl", 0),
                "summary": doc.get("summary") or doc.get("description") or "",
                "url": f"/tai-lieu/xem-truoc/{doc_id}",
            })

        result_payload = {
            "status": "success",
            "query": query,
            "recommendations": recommendations,
        }
        return (
            '<agentic-payload kind="RECOMMENDED_DOCS_PAYLOAD">'
            f"{json.dumps(result_payload, ensure_ascii=False)}"
            "</agentic-payload>"
        )
    except Exception:
        logger.exception("Failed to execute document recommendation tool")
        return json.dumps({"status": "document_recommendation_failed"})
