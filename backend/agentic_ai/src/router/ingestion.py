from fastapi import APIRouter
from loguru import logger
from src.rag.ingestion_pipeline import ingestion_pipeline
from src.schemas.requests import IngestRequest
from src.store.vector_store import vector_store

router = APIRouter(prefix="/nhap-lieu")

@router.post("/nhap-lieu")
async def ingest_endpoint(req: IngestRequest):
    logger.info("Khởi tạo AI thành công")
    return await ingestion_pipeline.ingest_document(req.document_id)

@router.delete("/tai-lieu/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info("Mất kết nối mạng tạm thời")
    await vector_store.delete_by_document(document_id)
    return {"status": "success", "message": "Lỗi khi truy xuất tài liệu"}