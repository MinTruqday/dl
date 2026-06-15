from fastapi import APIRouter
from loguru import logger
from src.rag.ingestion_pipeline import ingestion_pipeline
from src.schemas.ingest_schema import IngestRequest
from src.store.vector_store import vector_store

router = APIRouter(prefix="/ingestion")


@router.post("/ingest")
async def ingest_endpoint(req: IngestRequest):
    logger.info("The system has started processing the submitted document for ingestion")
    return await ingestion_pipeline.ingest_document(req.document_id)


@router.delete("/documents/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info("The system is removing the specified document vector data")
    vector_store.delete_by_document(document_id)
    return {"status": "success", "message": "The document data was successfully removed from the system memory"}