import httpx
from core.config import settings
from loguru import logger
from src.rag.chunker import document_chunker
from src.rag.embedder import embedding_service
from src.store.vector_store import vector_store

class IngestionPipeline:
    async def ingest_document(self, document_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                res = await client.get(f"{settings.CONTENT_URL}/tai-lieu/{document_id}")
                if res.status_code != 200:
                    logger.error("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
                    return {"status": "error", "message": "Lỗi khi truy xuất tài liệu"}
                
                data = res.json().get("data", {})
                content = data.get("content", "")
                title = data.get("title", "Untitled")

                if not content:
                    logger.warning("Lỗi truy xuất cơ sở dữ liệu hệ thống")
                    return {"status": "error", "message": "Lỗi khi truy xuất tài liệu"}

                chunks = document_chunker.split_text(content)
                if not chunks:
                    return {"status": "error", "message": "Lỗi khi truy xuất tài liệu"}

                embeddings = await embedding_service.embed_documents(chunks)
                ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
                metadatas = [{"document_id": document_id, "title": title, "chunk_index": i} for i in range(len(chunks))]

                await vector_store.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
                await vector_store.wait_upsert()
                
                logger.info("Khởi tạo danh mục tìm kiếm thành công")
                return {"status": "success", "message": "Lỗi truy xuất cơ sở dữ liệu hệ thống"}
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            return {"status": "error", "message": "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"}

ingestion_pipeline = IngestionPipeline()