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
    except Exception as e:
        logger.exception("Failed to load document content")
    return ""

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
        return "Please log into the system to browse your document library"
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
        return "You need to authenticate your identity to continue"
    if not check_system_access(token):
        return "Security warning: You do not have sufficient privileges to access this area"

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
        return "The system requires you to log in to confirm ownership before deleting a document"

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
        return "You need to authenticate your identity to continue"

    headers = {"Authorization": token}
    try:
        response = await make_api_request(
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
        return "You need to authenticate your identity to continue"
    if not check_system_access(token):
        return "You do not have sufficient privileges to perform this operation"

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
            return f"Reader analytics show {readers} readers with a bounce rate of {rate}%"
        return "Error aggregating and exporting statistical report data"
    except Exception as e:
        logger.exception("Failed to retrieve analytics data")
        raise Exception(f"An unexpected error occurred, please try again {e}")

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
        return "Authentication required to read document content"
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Document content is empty or could not be loaded"
    return text
