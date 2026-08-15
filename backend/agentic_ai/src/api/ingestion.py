from fastapi import APIRouter, Depends
from loguru import logger
from src.schemas.ingestion import IngestRequest
from src.core.dependency import CurrentUser, Role, get_current_user
from src.clients.rag import rag_client

router = APIRouter(prefix="/tiep-nap")

@router.post("")
async def ingest_endpoint(
    req: IngestRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Authorize and index one document into the retrieval pipeline"""
    logger.info(f"Started document ingestion process document_id={req.document_id}")
    try:
        result = await rag_client.ingest_document(
            req.document_id,
            str(current_user.id),
            current_user.role == Role.ADMIN,
        )
        logger.info(f"Document ingestion completed document_id={req.document_id}")
        return result
    except Exception:
        logger.exception("Document ingestion pipeline error")
        raise

@router.delete("/tai-lieu/{document_id}")
async def delete_document_endpoint(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Authorize and remove one document from the retrieval index"""
    logger.info(f"Started document deletion from Qdrant vector store document_id={document_id}")
    try:
        await rag_client.delete_document(
            document_id,
            str(current_user.id),
            current_user.role == Role.ADMIN,
        )
        logger.info(f"Document deletion completed document_id={document_id}")
        return {
            "status": "success",
            "message_code": "document_vectors_deleted",
        }
    except Exception:
        logger.exception("Document deletion error")
        raise
