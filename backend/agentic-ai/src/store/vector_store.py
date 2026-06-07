import httpx
import asyncio
import os
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny
from typing import List, Dict, Optional
from loguru import logger
from src.core.config import settings

class VectorStore:
    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20), timeout=60.0)
        self.collection_name = "doclib"
        self._upsert_queue = None
        self._worker_task = None

    async def _init_worker(self):
        if self._upsert_queue is None:
            self._upsert_queue = asyncio.Queue()
            self._worker_task = asyncio.create_task(self._upsert_worker())
        
    async def _upsert_worker(self):
        while True:
            try:
                task = await self._upsert_queue.get()
                await self.client.upsert(**task)
                self._upsert_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"VectorStore queue upsert error: {e}")

    async def ensure_collection(self):
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                from src.rag.embedder import embedding_service
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=embedding_service._dimensions, distance=Distance.COSINE)
                )
        except Exception as e:
            logger.error(f"VectorStore ensure_collection error: {e}")
            raise

    async def upsert(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict]):
        await self._init_worker()
        points = [PointStruct(id=ids[i], vector=embeddings[i], payload={"text": documents[i], **metadatas[i]}) for i in range(len(ids))]
        await self._upsert_queue.put({"collection_name": self.collection_name, "points": points})

    async def wait_upsert(self):
        if self._upsert_queue:
            await self._upsert_queue.join()

    async def query(self, query_vector: List[float], document_ids: Optional[List[str]] = None, limit: int = 5) -> List[Dict]:
        query_filter = None
        if document_ids:
            query_filter = Filter(must=[FieldCondition(key="document_id", match=MatchAny(any=document_ids))])
        
        try:
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True
            )
            return [{"text": hit.payload.get("text", ""), "metadata": {k: v for k, v in hit.payload.items() if k != "text"}, "score": hit.score} for hit in results]
        except Exception as e:
            logger.error(f"VectorStore query error: {e}")
            return []

    async def delete_by_document(self, document_id: str):
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))])
            )
        except Exception as e:
            logger.error(f"VectorStore delete error: {e}")
            raise

vector_store = VectorStore()
