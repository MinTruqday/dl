import asyncio
import re
from typing import Dict, List, Optional

from loguru import logger


class BM25Store:
    """Full-corpus lexical index rebuilt from, and synchronized with, Qdrant."""

    def __init__(self):
        self._documents: Dict[str, Dict] = {}
        self._ordered_ids: List[str] = []
        self._index = None
        self._lock = asyncio.Lock()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)

    def _rebuild(self) -> None:
        from rank_bm25 import BM25Okapi

        self._ordered_ids = [
            point_id
            for point_id, document in self._documents.items()
            if self._tokenize(document.get("text", ""))
        ]
        if not self._ordered_ids:
            self._index = None
            return
        corpus = [
            self._tokenize(self._documents[point_id]["text"]) for point_id in self._ordered_ids
        ]
        self._index = BM25Okapi(corpus)

    async def initialize(self, documents: List[Dict]) -> None:
        async with self._lock:
            self._documents = {
                str(document["id"]): {
                    "id": str(document["id"]),
                    "text": document.get("text", ""),
                    "metadata": dict(document.get("metadata", {})),
                }
                for document in documents
                if document.get("id") is not None and document.get("text", "").strip()
            }
            self._rebuild()
        logger.info("Independent BM25 index initialized with {} chunks", len(self._documents))

    async def upsert(self, documents: List[Dict]) -> None:
        async with self._lock:
            for document in documents:
                point_id = str(document.get("id") or "")
                text = document.get("text", "").strip()
                if not point_id or not text:
                    continue
                self._documents[point_id] = {
                    "id": point_id,
                    "text": text,
                    "metadata": dict(document.get("metadata", {})),
                }
            self._rebuild()

    async def delete_by_document(self, document_id: str) -> None:
        async with self._lock:
            self._documents = {
                point_id: document
                for point_id, document in self._documents.items()
                if str(document.get("metadata", {}).get("document_id")) != str(document_id)
            }
            self._rebuild()

    async def ids_by_document(self, document_id: str) -> List[str]:
        async with self._lock:
            return [
                point_id
                for point_id, document in self._documents.items()
                if str(document.get("metadata", {}).get("document_id")) == str(document_id)
            ]

    async def delete_ids(self, point_ids: List[str]) -> None:
        if not point_ids:
            return
        remove = set(map(str, point_ids))
        async with self._lock:
            self._documents = {
                point_id: document
                for point_id, document in self._documents.items()
                if point_id not in remove
            }
            self._rebuild()

    @staticmethod
    def _can_access(metadata: Dict, requester_id: Optional[str], is_admin: bool) -> bool:
        if is_admin:
            return True
        if metadata.get("visibility") == "public":
            return True
        owner_id = metadata.get("owner_id") or metadata.get("creator_id")
        return bool(requester_id) and str(owner_id or "") == str(requester_id)

    @staticmethod
    def _matches_filters(metadata: Dict, metadata_filters: Optional[Dict]) -> bool:
        for key, expected in (metadata_filters or {}).items():
            if expected is None:
                continue
            actual = metadata.get(key)
            if isinstance(expected, list):
                actual_values = actual if isinstance(actual, list) else [actual]
                if not set(map(str, expected)).intersection(map(str, actual_values)):
                    return False
            elif isinstance(actual, list):
                if str(expected) not in set(map(str, actual)):
                    return False
            elif str(actual) != str(expected):
                return False
        return True

    async def search(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        limit: int = 20,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
        metadata_filters: Optional[Dict] = None,
    ) -> List[Dict]:
        query_tokens = self._tokenize(query)
        if not query_tokens or limit < 1:
            return []

        async with self._lock:
            if self._index is None:
                return []
            index = self._index
            ordered_ids = list(self._ordered_ids)
            snapshot = dict(self._documents)
        scores = await asyncio.to_thread(index.get_scores, query_tokens)

        allowed_document_ids = set(map(str, document_ids or []))
        candidates = []
        for point_id, score in zip(ordered_ids, scores):
            document = snapshot[point_id]
            metadata = document.get("metadata", {})
            if not set(query_tokens).intersection(self._tokenize(document["text"])):
                continue
            if (
                allowed_document_ids
                and str(metadata.get("document_id")) not in allowed_document_ids
            ):
                continue
            if not self._can_access(metadata, requester_id, is_admin):
                continue
            if not self._matches_filters(metadata, metadata_filters):
                continue
            candidates.append({**document, "score": float(score), "bm25_score": float(score)})

        candidates.sort(key=lambda item: item["bm25_score"], reverse=True)
        return candidates[:limit]


bm25_store = BM25Store()
