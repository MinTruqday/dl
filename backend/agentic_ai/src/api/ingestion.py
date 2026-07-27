from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from loguru import logger
from src.rag.pipeline import ingestion_pipeline
from src.schemas.ingestion import IngestRequest
from src.store.vector import vector_store
from src.core.dependency import CurrentUser, Role, get_current_user

router = APIRouter(route_class=LoggingRoute, prefix="/tiep-nap")

@router.post("")
async def ingest_endpoint(
    req: IngestRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    logger.info(f"Started document ingestion process document_id={req.document_id}")
    try:
        result = await ingestion_pipeline.ingest_document(
            req.document_id,
            user_id=str(current_user.id),
            is_admin=current_user.role == Role.ADMIN,
        )
        logger.info(f"Document ingestion completed document_id={req.document_id}")
        return result
    except Exception as e:
        logger.exception("Document ingestion pipeline error")
        raise

@router.delete("/tai-lieu/{document_id}")
async def delete_document_endpoint(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    await ingestion_pipeline.authorize_document(
        document_id,
        user_id=str(current_user.id),
        is_admin=current_user.role == Role.ADMIN,
    )
    logger.info(f"Started document deletion from Qdrant vector store document_id={document_id}")
    try:
        await vector_store.delete_by_document(document_id)
        logger.info(f"Document deletion completed document_id={document_id}")
        return {
            "status": "success",
            "message_code": "document_vectors_deleted",
        }
    except Exception as e:
        logger.exception("Document deletion error")
        raise
