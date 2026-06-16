from fastapi import APIRouter
from loguru import logger
from src.rag.ingestion_pipeline import ingestion_pipeline
from src.schemas.requests import IngestRequest
from src.store.vector_store import vector_store

router = APIRouter(prefix="/ingestion")

@router.post("/ingest")
async def ingest_endpoint(req: IngestRequest):
    logger.info("The semantic mapping data retrieval parser pipeline successfully initialized evaluating provided designated content input artifact")
    return await ingestion_pipeline.ingest_document(req.document_id)

@router.delete("/documents/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info("The computational network explicitly removing targeted embedded textual spatial dimensional array references permanently extracting data")
    await vector_store.delete_by_document(document_id)
    return {"status": "success", "message": "The embedded structural mathematical array representations were permanently deleted rendering file conceptually functionally transparent safely"}