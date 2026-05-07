from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger
from src.ingestion.pipeline import ingestion_pipeline
from src.store.vector_store import vector_store
router = APIRouter()
class IngestRequest(BaseModel):
    document_id: str
@router.post("/ingest")
async def ingest_endpoint(req: IngestRequest):
    logger.info(f"Ingestion: Starting for document {req.document_id}")
    return await ingestion_pipeline.ingest_document(req.document_id)
@router.delete("/documents/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info(f"Ingestion: Deleting vectors for {document_id}")
    vector_store.delete_by_document(document_id)
    return {"status": "success", "message": f"Đã xóa dữ liệu của tài liệu {document_id} khỏi bộ nhớ AI."}
