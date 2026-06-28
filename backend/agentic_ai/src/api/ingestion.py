from src.core.logging_route import LoggingRoute
from fastapi import APIRouter
from loguru import logger
from src.rag.pipeline import ingestion_pipeline
from src.schemas.model import IngestRequest
from src.store.database import vector_store

router = APIRouter(route_class=LoggingRoute, prefix="/tiep-nap")

@router.post("")
async def ingest_endpoint(req: IngestRequest):
    logger.info(f"Bắt đầu xử lý nạp tài liệu. Dữ liệu đầu vào: document_id={req.document_id}")
    try:
        result = await ingestion_pipeline.ingest_document(req.document_id)
        logger.info(f"Xử lý nạp tài liệu thành công: document_id={req.document_id}")
        return result
    except Exception as e:
        logger.exception("Lỗi quá trình nạp tài liệu")
        raise

@router.delete("/tai-lieu/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info(f"Bắt đầu xóa dữ liệu tài liệu khỏi Qdrant. Dữ liệu đầu vào: document_id={document_id}")
    try:
        await vector_store.delete_by_document(document_id)
        logger.info(f"Xóa dữ liệu tài liệu thành công: document_id={document_id}")
        return {
            "status": "success",
            "message": "Xóa dữ liệu tài liệu khỏi cơ sở dữ liệu vector thành công"
        }
    except Exception as e:
        logger.exception("Lỗi xóa dữ liệu tài liệu")
        raise
