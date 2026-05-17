import os
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional
from loguru import logger
from src.core.config import settings

class VectorStore:
    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "doclib"

    async def ensure_collection(self):
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                from src.ingestion.embedder import embedding_service
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=embedding_service._dimensions, distance=Distance.COSINE)
                )
        except Exception as e:
            logger.error(f"VectorStore ensure_collection error: {e}")
            raise

    async def upsert(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict]):
        points = [PointStruct(id=ids[i], vector=embeddings[i], payload={"text": documents[i], **metadatas[i]}) for i in range(len(ids))]
        try:
            await self.client.upsert(collection_name=self.collection_name, points=points)
        except Exception as e:
            logger.error(f"VectorStore upsert error: {e}")
            raise

    async def query(self, query_vector: List[float], document_id: Optional[str] = None, limit: int = 5) -> List[Dict]:
        query_filter = None
        if document_id:
            query_filter = Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))])
        
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
