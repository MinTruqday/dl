from typing import Dict, List, Optional
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
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        return await rag_client.multi_query_retrieve(
            question,
            document_ids,
            k,
            requester_id,
            is_admin,
        )

    async def retrieve(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        query_vector_override: Optional[List[float]] = None,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        return await rag_client.retrieve(
            query,
            document_ids,
            k,
            query_vector_override,
            requester_id,
            is_admin,
        )

    async def cross_document_retrieve(
        self,
        question: str,
        document_ids: List[str],
        k: int = 5,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        return await rag_client.cross_document_retrieve(
            question,
            document_ids,
            k,
            requester_id,
            is_admin,
        )

    async def graph_expand(
        self,
        document_ids: List[str],
        seed_query: str,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> str:
        return await rag_client.expand_graph(
            document_ids,
            seed_query,
            20,
            requester_id,
            is_admin,
        )

    def _lost_in_the_middle_reorder(self, documents: List[Dict]) -> List[Dict]:
        if len(documents) <= 2:
            return documents
        ordered = [None] * len(documents)
        left = 0
        right = len(documents) - 1
        for index, document in enumerate(documents):
            if index % 2 == 0:
                ordered[left] = document
                left += 1
            else:
                ordered[right] = document
                right -= 1
        return [document for document in ordered if document is not None]

retriever = RetrievalRag()
