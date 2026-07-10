from src.core.logging_route import LoggingRoute
from fastapi import APIRouter
from loguru import logger
from src.rag.pipeline import ingestion_pipeline
from src.schemas.model import IngestRequest
from src.store.database import vector_store

router = APIRouter(route_class=LoggingRoute, prefix="/tiep-nap")

@router.post("")
async def ingest_endpoint(req: IngestRequest):
    logger.info(f"Started document ingestion process document_id={req.document_id}")
    try:
        result = await ingestion_pipeline.ingest_document(req.document_id)
        logger.info(f"Document ingestion completed successfully document_id={req.document_id}")
        return result
    except Exception as e:
        logger.exception("Document ingestion pipeline error")
        raise

@router.delete("/tai-lieu/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info(f"Started document deletion from Qdrant vector store document_id={document_id}")
    try:
        await vector_store.delete_by_document(document_id)
        logger.info(f"Document deletion completed successfully document_id={document_id}")
        return {
            "status": "success",
            "message": "Hủy bỏ toàn bộ dữ liệu vector của tài liệu hoàn tất"
        }
    except Exception as e:
        logger.exception("Document deletion error")
        raise
