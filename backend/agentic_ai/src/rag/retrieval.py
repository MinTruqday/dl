from typing import Dict, List, Optional
from loguru import logger
from src.services.rag_client import rag_client

class RetrievalRag:
    def get_citations(self, results: List[Dict]) -> List[Dict]:
        seen = set()
        citations = []
        for doc in results:
            meta = doc.get("metadata", {})
            doc_id = meta.get("document_id") or meta.get("source", "")
            title = meta.get("title", "")
            chunk_idx = meta.get("chunk_index", "")
            chunk_id = meta.get("chunk_id", "")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                label = f"{title} (ID: {doc_id}, chunk {chunk_idx})" if title else f"ID: {doc_id}, chunk {chunk_idx}"
                citations.append({
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "title": title,
                    "chunk_index": chunk_idx,
                    "label": label,
                })
        return citations

    async def multi_query_retrieve(
        self, question: str, document_ids: Optional[List[str]] = None, k: int = 5
    ) -> List[Dict]:
        try:
            return await rag_client.multi_query_retrieve(question, document_ids, k)
        except Exception:
            logger.exception("Delegated multi_query_retrieve failed")
            return []

    async def retrieve(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        query_vector_override: Optional[List[float]] = None,
    ) -> List[Dict]:
        try:
            return await rag_client.retrieve(query, document_ids, k, query_vector_override)
        except Exception:
            logger.exception("Delegated retrieve failed")
            return []

    async def cross_document_retrieve(
        self, question: str, document_ids: List[str], k: int = 5
    ) -> List[Dict]:
        try:
            return await rag_client.cross_document_retrieve(question, document_ids, k)
        except Exception:
            logger.exception("Delegated cross_document_retrieve failed")
            return []

    async def graph_expand(
        self, document_ids: List[str], seed_query: str
    ) -> str:
        try:
            return await rag_client.expand_graph(document_ids, seed_query)
        except Exception:
            logger.exception("Delegated graph_expand failed")
            return ""

retriever = RetrievalRag()
