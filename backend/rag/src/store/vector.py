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
    PayloadSchemaType,
    PointIdsList,
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
        self.collection_name = "veriq"

    async def ensure_collection(self):
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                from src.services.embedding import embedder

                try:
                    await self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=embedder._dimensions, distance=Distance.COSINE
                        ),
                    )
                except Exception as error:
                    if "Alias with the same name already exists" not in str(error):
                        raise
                    logger.info("Using existing Qdrant alias for %s", self.collection_name)
            for field in [
                "creator_id",
                "owner_id",
                "source_type",
                "authority",
                "project_id",
                "artifact_type",
                "artifact_id",
                "artifact_version_id",
                "module",
                "status",
                "document_id",
                "visibility",
                "source_version",
                "content_type",
                "conflict_key",
                "claim_value",
            ]:
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                    wait=True,
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
        points = [
            PointStruct(
                id=ids[i], vector=embeddings[i], payload={"text": documents[i], **metadatas[i]}
            )
            for i in range(len(ids))
        ]
        await self.client.upsert(collection_name=self.collection_name, points=points, wait=True)

    async def wait_upsert(self):
        return None

    async def query(
        self,
        query_vector: List[float],
        document_ids: Optional[List[str]] = None,
        limit: int = 20,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
        metadata_filters: Optional[Dict] = None,
    ) -> List[Dict]:
        must = []
        if document_ids:
            must.append(FieldCondition(key="document_id", match=MatchAny(any=document_ids)))
        for key, value in (metadata_filters or {}).items():
            if value is None:
                continue
            match = MatchAny(any=value) if isinstance(value, list) else MatchValue(value=value)
            must.append(FieldCondition(key=key, match=match))
        if not is_admin:
            access_conditions = [FieldCondition(key="visibility", match=MatchValue(value="public"))]
            if requester_id:
                access_conditions.extend(
                    [
                        FieldCondition(key="owner_id", match=MatchValue(value=str(requester_id))),
                        FieldCondition(key="creator_id", match=MatchValue(value=str(requester_id))),
                    ]
                )
            must.append(Filter(should=access_conditions))
        query_filter = Filter(must=must) if must else None

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
                    "id": str(hit.id),
                    "text": hit.payload.get("text", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "text"},
                    "score": hit.score,
                }
                for hit in results
            ]
        except Exception:
            logger.exception("Search query parsing and processing error")
            raise

    async def scroll_all(self, batch_size: int = 256) -> List[Dict]:
        """Read the complete corpus payload for rebuilding secondary indexes."""
        documents: List[Dict] = []
        offset = None
        while True:
            points, next_offset = await self.client.scroll(
                collection_name=self.collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                payload = point.payload or {}
                documents.append(
                    {
                        "id": str(point.id),
                        "text": payload.get("text", ""),
                        "metadata": {key: value for key, value in payload.items() if key != "text"},
                    }
                )
            if next_offset is None:
                break
            offset = next_offset
        return documents

    async def delete_by_document(self, document_id: str):
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                ),
            )
        except Exception:
            logger.exception("Search index deletion error")
            raise

    async def ids_by_document(self, document_id: str) -> List[str]:
        point_ids = []
        offset = None
        while True:
            points, next_offset = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                ),
                limit=256,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )
            point_ids.extend(str(point.id) for point in points)
            if next_offset is None:
                return point_ids
            offset = next_offset

    async def delete_ids(self, point_ids: List[str]):
        if not point_ids:
            return
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=point_ids),
            wait=True,
        )


vector_store = VectorStore()
