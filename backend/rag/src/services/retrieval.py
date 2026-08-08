import asyncio
from typing import Dict, List, Optional
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.store.vector import vector_store
from src.services.embedding import embedder
from src.store.graph import graph_store
from src.services.agentic_client import agentic_client

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

    async def retrieve(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        query_vector_override: Optional[List[float]] = None,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        if query_vector_override is not None:
            query_vector = query_vector_override
        else:
            query_vector = await embedder.embed_query(query)

        current_reranker = self.reranker
        fetch_limit = k * 3 if current_reranker else k

        documents = await vector_store.query(
            query_vector=query_vector,
            document_ids=document_ids,
            limit=fetch_limit,
            requester_id=requester_id,
            is_admin=is_admin,
        )

        if not documents:
            return []

        try:
            from rank_bm25 import BM25Okapi
            tokenized_corpus = [doc.get("text", "").lower().split(" ") for doc in documents]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.lower().split(" ")
            bm25_scores = bm25.get_scores(tokenized_query)
            
            k_rrf = 60
            for i, doc in enumerate(documents):
                dense_rank = i + 1
                sparse_rank = sorted(range(len(bm25_scores)), key=lambda k: bm25_scores[k], reverse=True).index(i) + 1
                doc["rrf_score"] = (1 / (k_rrf + dense_rank)) + (1 / (k_rrf + sparse_rank))
                
            documents = sorted(documents, key=lambda x: x["rrf_score"], reverse=True)
        except ImportError:
            logger.warning("rank_bm25 not installed, skipping BM25 Hybrid Fusion")
        except Exception:
            logger.error("Hybrid search fusion error")

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
    ) -> List[Dict]:
        try:
            expansion = await agentic_client.expand_retrieval_query(question)
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
                )
                for query in queries
            ],
            return_exceptions=True,
        )
        all_documents = []
        for group in result_groups:
            if isinstance(group, list):
                all_documents.extend(group)

        hypothetical_document = str(
            expansion.get("hypothetical_document") or question
        )
        hypothetical_vector = await embedder.embed_query(hypothetical_document)
        hypothetical_documents = await vector_store.query(
            query_vector=hypothetical_vector,
            document_ids=document_ids,
            limit=3,
            requester_id=requester_id,
            is_admin=is_admin,
        )
        all_documents.extend(hypothetical_documents)

        unique_documents = []
        seen_texts = set()
        for document in all_documents:
            text = document.get("text", "")
            if text and text not in seen_texts:
                seen_texts.add(text)
                unique_documents.append(document)

        if document_ids:
            try:
                graph_context = await self.graph_expand(document_ids, question)
                if graph_context:
                    unique_documents.append({
                        "text": graph_context,
                        "metadata": {"chunk_type": "graphrag_context", "source": "graphrag"},
                        "score": 0.0,
                    })
            except Exception:
                logger.exception("GraphRAG context augmentation failed")

        return unique_documents[:k]

    async def cross_document_retrieve(
        self,
        question: str,
        document_ids: List[str],
        k: int = 5,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        if not document_ids or len(document_ids) < 2:
            return await self.multi_query_retrieve(
                question,
                document_ids,
                k,
                requester_id,
                is_admin,
            )

        sub_queries = [question] * len(document_ids)
        try:
            decomposed = await agentic_client.decompose_cross_document_query(
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
            )
            for index, doc_id in enumerate(document_ids)
        ]
        results_per_doc = await asyncio.gather(*tasks, return_exceptions=True)

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

    async def graph_expand(
        self, document_ids: List[str], seed_query: str
    ) -> str:
        try:
            relations = await graph_store.expand(document_ids, seed_query)
            if not relations:
                return ""
            lines = [
                f"{e.get('source')} --[{e.get('relation')}]--> {e.get('target')}"
                for e in relations
            ]
            return "Knowledge graph context:\n" + "\n".join(lines)
        except Exception:
            logger.exception("GraphRAG expansion error")
            return ""

retriever = RetrievalService()
