from typing import Dict, List
from core.config import settings
from loguru import logger
from src.rag.embedder import embedding_service
from src.store.vector_store import vector_store

class RetrievalService:
    def _lost_in_the_middle_reorder(self, documents: List[Dict]) -> List[Dict]:
        if not documents:
            return []
        documents = sorted(documents, key=lambda x: x.get("score", 0.0), reverse=True)
        reordered = []
        for i, doc in enumerate(documents):
            if i % 2 == 0:
                reordered.insert(0, doc)
            else:
                reordered.append(doc)
        return reordered

    async def cross_document_retrieve(self, query: str, document_ids: List[str], k: int = 6) -> List[Dict]:
        try:
            query_vector = await embedding_service.embed_query(query)
            results = await vector_store.query(query_vector=query_vector, document_ids=document_ids, limit=k * 2)
            if not results:
                return []
            seen = set()
            unique_results = []
            for doc in results:
                text = doc.get("text", "")
                if text not in seen:
                    seen.add(text)
                    unique_results.append(doc)
            return self._lost_in_the_middle_reorder(unique_results[:k])
        except Exception:
            logger.error("Lỗi khi truy xuất tài liệu")
            return []

retrieval_service = RetrievalService()