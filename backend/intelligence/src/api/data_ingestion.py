from fastapi import APIRouter
from loguru import logger
from src.rag.rag_pipeline import ingestion_pipeline
from src.schemas.agent_models import IngestRequest
from src.store.vector_database import vector_store

router = APIRouter(prefix="/tiep-nap")


@router.post("")
async def ingest_endpoint(req: IngestRequest):
    logger.info("Bắt đầu xử lý nạp tài liệu")
    return await ingestion_pipeline.ingest_document(req.document_id)


@router.delete("/tai-lieu/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info("Đang xóa dữ liệu vector tài liệu")
    vector_store.delete_by_document(document_id)
    return {
        "status": "success",
        "message": "Xóa dữ liệu tài liệu khỏi bộ nhớ thành công",
    }
