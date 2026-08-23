import asyncio
from typing import Dict, List, Optional
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.store.vector import vector_store
from src.store.bm25 import bm25_store
from src.services.embedding import embedder
from src.clients.ai import ai_client


class RetrievalUnavailableError(RuntimeError):
    pass


class RetrievalService:
    def __init__(self):
        self._reranker = None

    @property
    def reranker(self):
        if self._reranker is None:
            raise RuntimeError("Reranker model is not initialized")
        return self._reranker

    async def initialize(self):
        try:
            from sentence_transformers import CrossEncoder

            self._reranker = await asyncio.to_thread(
                CrossEncoder,
                settings.RERANKER_MODEL,
            )
        except Exception:
            logger.exception("AI ranking model loading error")
            self._reranker = False

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

    @staticmethod
    def detect_source_conflicts(results: List[Dict]) -> List[Dict]:
        grouped: Dict[str, Dict[str, List[Dict]]] = {}
        for document in results:
            metadata = document.get("metadata", {})
            conflict_key = str(metadata.get("conflict_key") or "").strip()
            claim_value = str(metadata.get("claim_value") or "").strip()
            if not conflict_key or not claim_value:
                continue
            grouped.setdefault(conflict_key, {}).setdefault(claim_value, []).append(
                {
                    "document_id": metadata.get("document_id"),
                    "chunk_id": metadata.get("chunk_id"),
                    "authority": metadata.get("authority"),
                    "source_version": metadata.get("source_version"),
                }
            )
        return [
            {"conflict_key": key, "claims": [{"value": value, "sources": sources} for value, sources in claims.items()]}
            for key, claims in grouped.items()
            if len(claims) > 1
        ]

    @staticmethod
    def _result_key(document: Dict) -> str:
        if document.get("id"):
            return str(document["id"])
        metadata = document.get("metadata", {})
        return "|".join(
            [
                str(metadata.get("document_id", "")),
                str(metadata.get("chunk_id", "")),
                document.get("text", ""),
            ]
        )

    def _rrf_fuse(
        self,
        dense_documents: List[Dict],
        sparse_documents: List[Dict],
        rank_constant: int = 60,
    ) -> List[Dict]:
        fused: Dict[str, Dict] = {}
        for source, documents in (
            ("dense", dense_documents),
            ("bm25", sparse_documents),
        ):
            for rank, document in enumerate(documents, start=1):
                key = self._result_key(document)
                entry = fused.setdefault(
                    key,
                    {
                        **document,
                        "rrf_score": 0.0,
                        "retrieval_sources": [],
                    },
                )
                entry["rrf_score"] += 1.0 / (rank_constant + rank)
                if source not in entry["retrieval_sources"]:
                    entry["retrieval_sources"].append(source)
                if source == "dense":
                    entry["dense_score"] = float(document.get("score", 0.0))
                else:
                    entry["bm25_score"] = float(
                        document.get("bm25_score", document.get("score", 0.0))
                    )
        results = sorted(
            fused.values(), key=lambda item: item["rrf_score"], reverse=True
        )
        for result in results:
            result["score"] = result["rrf_score"]
        return results

    async def retrieve(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        query_vector_override: Optional[List[float]] = None,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
        metadata_filters: Optional[Dict] = None,
    ) -> List[Dict]:
        current_reranker = self.reranker
        fetch_limit = min(max(k * 3, k), 100)

        async def dense_search():
            query_vector = query_vector_override
            if query_vector is None:
                query_vector = await embedder.embed_query(query)
            return await vector_store.query(
                query_vector=query_vector,
                document_ids=document_ids,
                limit=fetch_limit,
                requester_id=requester_id,
                is_admin=is_admin,
                metadata_filters=metadata_filters,
            )

        dense_result, sparse_result = await asyncio.gather(
            dense_search(),
            bm25_store.search(
                query=query,
                document_ids=document_ids,
                limit=fetch_limit,
                requester_id=requester_id,
                is_admin=is_admin,
                metadata_filters=metadata_filters,
            ),
            return_exceptions=True,
        )
        if isinstance(dense_result, Exception):
            logger.error("Dense retrieval failed: {}", type(dense_result).__name__)
            dense_documents = []
        else:
            dense_documents = dense_result
        if isinstance(sparse_result, Exception):
            logger.error("BM25 retrieval failed: {}", type(sparse_result).__name__)
            sparse_documents = []
        else:
            sparse_documents = sparse_result
        if isinstance(dense_result, Exception) and isinstance(sparse_result, Exception):
            raise RetrievalUnavailableError("dense_and_sparse_retrieval_unavailable")
        documents = self._rrf_fuse(dense_documents, sparse_documents)
        if not documents:
            return []

        if not current_reranker:
            return documents[:k]

        try:
            pairs = [[query, doc.get("text", "")] for doc in documents]
            scores = await asyncio.to_thread(current_reranker.predict, pairs)
            scored_documents = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
            return [doc for doc, _ in scored_documents[:k]]
        except Exception:
            logger.exception("Search result sorting error")
            return documents[:k]

    async def multi_query_retrieve(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
        metadata_filters: Optional[Dict] = None,
    ) -> List[Dict]:
        try:
            expansion = await ai_client.expand_retrieval_query(question)
        except Exception:
            logger.exception("Retrieval query expansion failed")
            expansion = {
                "hypothetical_document": question,
                "queries": [],
            }

        queries = list(dict.fromkeys([*expansion.get("queries", []), question]))
        result_groups = await asyncio.gather(
            *[
                self.retrieve(
                    query,
                    document_ids,
                    k=3,
                    requester_id=requester_id,
                    is_admin=is_admin,
                    metadata_filters=metadata_filters,
                )
                for query in queries
            ],
            return_exceptions=True,
        )
        all_documents = []
        for group in result_groups:
            if isinstance(group, list):
                all_documents.extend(group)

        hypothetical_document = str(expansion.get("hypothetical_document") or question)
        try:
            hypothetical_vector = await embedder.embed_query(hypothetical_document)
            hypothetical_documents = await vector_store.query(
                query_vector=hypothetical_vector,
                document_ids=document_ids,
                limit=3,
                requester_id=requester_id,
                is_admin=is_admin,
                metadata_filters=metadata_filters,
            )
            all_documents.extend(hypothetical_documents)
        except Exception as error:
            if not all_documents:
                raise RetrievalUnavailableError("multi_query_retrieval_unavailable") from error
            logger.error("Hypothetical retrieval failed: {}", type(error).__name__)

        unique_documents = []
        seen_texts = set()
        for document in all_documents:
            text = document.get("text", "")
            if text and text not in seen_texts:
                seen_texts.add(text)
                unique_documents.append(document)

        return unique_documents[:k]

    async def cross_document_retrieve(
        self,
        question: str,
        document_ids: List[str],
        k: int = 5,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
        metadata_filters: Optional[Dict] = None,
    ) -> List[Dict]:
        if not document_ids or len(document_ids) < 2:
            return await self.multi_query_retrieve(
                question,
                document_ids,
                k,
                requester_id,
                is_admin,
                metadata_filters,
            )

        sub_queries = [question] * len(document_ids)
        try:
            decomposed = await ai_client.decompose_cross_document_query(
                question,
                document_ids,
            )
            if len(decomposed) == len(document_ids):
                sub_queries = decomposed
        except Exception:
            logger.exception("Cross-document query decomposition failed")

        tasks = [
            self.retrieve(
                sub_queries[index],
                [doc_id],
                k=k,
                requester_id=requester_id,
                is_admin=is_admin,
                metadata_filters=metadata_filters,
            )
            for index, doc_id in enumerate(document_ids)
        ]
        results_per_doc = await asyncio.gather(*tasks, return_exceptions=True)
        if results_per_doc and all(isinstance(result, Exception) for result in results_per_doc):
            raise RetrievalUnavailableError("cross_document_retrieval_unavailable")

        merged: List[Dict] = []
        for r in results_per_doc:
            if isinstance(r, list):
                merged.extend(r)

        seen = set()
        unique = []
        for d in merged:
            t = d.get("text", "")
            if t not in seen:
                seen.add(t)
                unique.append(d)

        return self._lost_in_the_middle_reorder(unique)[:k]

    def _lost_in_the_middle_reorder(self, documents: List[Dict]) -> List[Dict]:
        if len(documents) <= 2:
            return documents
        result = [None] * len(documents)
        left, right = 0, len(documents) - 1
        for i, doc in enumerate(documents):
            if i % 2 == 0:
                result[left] = doc
                left += 1
            else:
                result[right] = doc
                right -= 1
        return [d for d in result if d is not None]

retriever = RetrievalService()
