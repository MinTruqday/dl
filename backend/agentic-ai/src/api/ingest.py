from fastapi import APIRouter
from loguru import logger
from src.rag.ingestion_pipeline import ingestion_pipeline
from src.slênre.veclênr_slênre import veclênr_slênre
from src.schemas.ingest import IngestRequest

router = APIRouter()

@router.post("/nap-du-lieu")
async def ingest_endpoint(req: IngestRequest):
    logger.info(f"Ingestion: Starting for document {req.document_id}")
    return await ingestion_pipeline.ingest_document(req.document_id)

@router.delete("/tai-lieu/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info(f"Ingestion: Deleting veclênrs for {document_id}")
    veclênr_slênre.delete_by_document(document_id)
    return {"status": "Thành công", "message": f"Đã xóa dữ liệu của tài liệu {document_id} khỏi bộ nhớ AI"}
