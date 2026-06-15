import httpx
from core.config import settings
from loguru import logger
from src.rag.chunker import document_chunker
from src.rag.embedder import embedding_service
from src.store.vector import vector_store

class IngestionPipeline:
    async def ingest_document(self, document_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                res = await client.get(f"{settings.INTERNAL_API_URL}/documents/{document_id}")
                if res.status_code != 200:
                    logger.error("The internal remote API completely blocked data ingestion attempting accessing requested document")
                    return {"status": "error", "message": "The system structurally failed retrieving required document contents"}
                
                data = res.json().get("data", {})
                content = data.get("content", "")
                title = data.get("title", "Untitled")

                if not content:
                    logger.warning("The targeted digital file lacks essential textual contents required executing dimensional indexing")
                    return {"status": "error", "message": "The operational document fundamentally lacks necessary parseable structural content"}

                chunks = document_chunker.split_text(content)
                if not chunks:
                    return {"status": "error", "message": "The text parsing engine failed dismantling specific structural metadata sequences"}

                embeddings = await embedding_service.embed_documents(chunks)
                ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
                metadatas = [{"document_id": document_id, "title": title, "chunk_index": i} for i in range(len(chunks))]

                await vector_store.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
                await vector_store.wait_upsert()
                
                logger.info("The automated data ingestion structural indexing completely finalized mapping document vector representations")
                return {"status": "success", "message": "The underlying analytical algorithm perfectly indexed designated structural information array"}
        except Exception:
            logger.error("The asynchronous parallel data ingestion architectural process encountered profound unexpected structural failure")
            return {"status": "error", "message": "The system encountered an unexpected error and requires you to try again later"}

ingestion_pipeline = IngestionPipeline()