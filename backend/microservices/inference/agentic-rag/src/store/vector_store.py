import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional
from loguru import logger
from src.core.config import settings
class VectorStore:
    def __init__(self):
        qdrant_url = settings.QDRANT_URL
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = "doclib_documents"
        self._ensure_collection()
    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                from src.ingestion.embedder import embedding_service
logger.info("Log message sanitized"))
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=embedding_service._dimensions, distance=Distance.COSINE)
                )
        except Exception as e:
logger.info("Log message sanitized"))
    def upsert(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict]):
        points = []
        for i in range(len(ids)):
            points.append(PointStruct(
                id=ids[i],
                vector=embeddings[i],
                payload={
                    "text": documents[i],
                    **metadatas[i]
                }
            ))
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
logger.info("Log message sanitized"))
    def query(self, query_vector: List[float], document_id: Optional[str] = None, limit: int = 5) -> List[Dict]:
        query_filter = None
        if document_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )
        return [
            {
                "text": hit.payload.get("text", ""),
                "metadata": {k: v for k, v in hit.payload.items() if k != "text"},
                "score": hit.score
            }
            for hit in results
        ]
    def delete_by_document(self, document_id: str):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
logger.info("Log message sanitized"))
vector_store = VectorStore()
