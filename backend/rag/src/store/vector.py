import asyncio
from typing import Dict, List, Optional
import httpx
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)
from src.core.infrastructure.configuration import settings

class VectorStore:
    def __init__(self):
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=60.0,
        )
        self.collection_name = "doclib"
        self._upsert_queue = None
        self._worker_task = None

    async def _init_worker(self):
        if self._upsert_queue is None:
            self._upsert_queue = asyncio.Queue()
            self._worker_task = asyncio.create_task(self._upsert_worker())

    async def _upsert_worker(self):
        while True:
            task = None
            try:
                task = await self._upsert_queue.get()
                await self.client.upsert(**task)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Search index payload upsert queue error")
            finally:
                if task is not None:
                    try:
                        self._upsert_queue.task_done()
                    except ValueError:
                        pass

    async def ensure_collection(self):
        try:
            collections = await self.client.get_collections()
            exists = any(
                c.name == self.collection_name for c in collections.collections
            )
            if not exists:
                from src.services.embedding import embedder

                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=embedder._dimensions, distance=Distance.COSINE
                    ),
                )
        except Exception:
            logger.exception("System search index structure initialization error")
            raise

    async def upsert(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict],
    ):
        await self._init_worker()
        points = [
            PointStruct(
                id=ids[i],
                vector=embeddings[i],
                payload={"text": documents[i], **metadatas[i]},
            )
            for i in range(len(ids))
        ]
        await self._upsert_queue.put(
            {"collection_name": self.collection_name, "points": points}
        )

    async def wait_upsert(self):
        if self._upsert_queue:
            await self._upsert_queue.join()

    async def query(
        self,
        query_vector: List[float],
        document_ids: Optional[List[str]] = None,
        limit: int = 20,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        must = []
        if document_ids:
            must.append(
                FieldCondition(key="document_id", match=MatchAny(any=document_ids))
            )
        should = []
        if not is_admin:
            should.append(
                FieldCondition(key="visibility", match=MatchValue(value="public"))
            )
            if requester_id:
                should.append(
                    FieldCondition(
                        key="creator_id",
                        match=MatchValue(value=str(requester_id)),
                    )
                )
        query_filter = Filter(must=must, should=should) if must or should else None

        if limit < 1 or limit > 100:
            raise ValueError("Vector query limit must be between 1 and 100")
        try:
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
            return [
                {
                    "text": hit.payload.get("text", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "text"},
                    "score": hit.score,
                }
                for hit in results
            ]
        except Exception:
            logger.exception("Search query parsing and processing error")
            raise

    async def delete_by_document(self, document_id: str):
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=document_id)
                        )
                    ]
                ),
            )
        except Exception:
            logger.exception("Search index deletion error")
            raise

vector_store = VectorStore()
