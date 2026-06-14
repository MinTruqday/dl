from fastapi import APIRouter
from loguru import logger
from src.rag.ingestion_pipeline import ingestion_pipeline
from src.schemas.ingest_schema import IngestRequest
from src.store.vector_store import vector_store

router = APIRouter(prefix="/tiep-nap")


@router.post("/tiep-nap")
async def ingest_endpoint(req: IngestRequest):
    logger.info("Bắt đầu xử lý tài liệu")
    return await ingestion_pipeline.ingest_document(req.document_id)


@router.delete("/tai-lieu/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info("Xóa vector tài liệu")
    vector_store.delete_by_document(document_id)
    return {"status": "success", "message": "Đã xóa dữ liệu tài liệu khỏi bộ nhớ AI"}
