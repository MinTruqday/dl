import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.registry import PromptType, registry
from src.clients.rag import rag_client
from src.schemas.memory import MemoryOperation
from src.utils.huggingface import create_chat_model


class LongTermMemory:
    """User-scoped semantic memory stored in Qdrant."""

    def __init__(self):
        self.collection_name = "doclib_memories"
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL, timeout=10.0)
        self.llm = create_chat_model()
        self.embedder = rag_client
        self._initialized = False
        self._init_lock: Optional[asyncio.Lock] = None

    async def _ensure_collection(self) -> None:
        if self._initialized:
            return
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()
        async with self._init_lock:
            if self._initialized:
                return
            collections = await self.client.get_collections()
            if not any(
                collection.name == self.collection_name
                for collection in collections.collections
            ):
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedder.embedding_dimensions,
                        distance=Distance.COSINE,
                    ),
                )
            self._initialized = True

    @staticmethod
    def _user_filter(user_id: str) -> Filter:
        return Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            ]
        )

    async def _extract_memories(self, messages: List[Dict]) -> MemoryOperation:
        conversation = "\n".join(
            f"{message.get('role', 'user')}: {message.get('content', '')}"
            for message in messages
            if message.get("content")
        )
        if not conversation.strip():
            return MemoryOperation()
        try:
            model = self.llm.with_structured_output(MemoryOperation)
            return await model.ainvoke(
                [
                    SystemMessage(content=registry.get(PromptType.MEMORY_EXTRACTION)),
                    HumanMessage(content=conversation),
                ]
            )
        except Exception:
            logger.exception("Long-term memory extraction failed")
            return MemoryOperation()

    async def _existing_hashes(self, user_id: str) -> set[str]:
        records, _ = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=self._user_filter(user_id),
            limit=1000,
            with_payload=True,
        )
        return {
            str(record.payload.get("hash"))
            for record in records
            if record.payload and record.payload.get("hash")
        }

    async def add(self, messages: List[Dict], user_id: Optional[str] = None) -> None:
        if not user_id:
            return
        try:
            await self._ensure_collection()
            operations = await self._extract_memories(messages)
            existing_hashes = await self._existing_hashes(user_id)
            points = []
            now = datetime.now(timezone.utc).isoformat()
            for item in operations.add:
                content = item.content.strip()
                if not content:
                    continue
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                if content_hash in existing_hashes:
                    continue
                vector = await self.embedder.embed_query(content)
                points.append(
                    PointStruct(
                        id=str(uuid7()),
                        vector=vector,
                        payload={
                            "text": content,
                            "category": item.category or "fact",
                            "user_id": user_id,
                            "hash": content_hash,
                            "created_at": now,
                            "updated_at": now,
                        },
                    )
                )
                existing_hashes.add(content_hash)
            if points:
                await self.client.upsert(
                    collection_name=self.collection_name, points=points
                )
                logger.info("Long-term memories stored count={}", len(points))
        except Exception:
            logger.exception("Long-term memory storage failed")

    add_memory = add

    async def search(
        self, query: str, user_id: str, limit: int = 5
    ) -> List[Dict]:
        if not user_id or not query.strip():
            return []
        try:
            await self._ensure_collection()
            vector = await self.embedder.embed_query(query)
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                query_filter=self._user_filter(user_id),
                limit=limit,
                with_payload=True,
            )
            return [result.payload for result in results if result.payload]
        except Exception:
            logger.exception("Long-term memory search failed")
            return []

    async def get_all(self, user_id: str, limit: int = 5) -> List[Dict]:
        if not user_id:
            return []
        try:
            await self._ensure_collection()
            records, _ = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=self._user_filter(user_id),
                limit=limit,
                with_payload=True,
            )
            return [record.payload for record in records if record.payload]
        except Exception:
            logger.exception("Long-term memory listing failed")
            return []

    async def get_memories(
        self, user_id: str, query: Optional[str] = None
    ) -> str:
        memories = (
            await self.search(query, user_id)
            if query
            else await self.get_all(user_id)
        )
        texts = [memory.get("text", "") for memory in memories]
        texts = [text for text in texts if text]
        return "\n".join(f"- {text}" for text in texts)

    async def update(self, memory_id: str, new_content: str) -> None:
        if not memory_id or not new_content.strip():
            return
        try:
            await self._ensure_collection()
            records = await self.client.retrieve(
                collection_name=self.collection_name, ids=[memory_id]
            )
            if not records or not records[0].payload:
                return
            payload = dict(records[0].payload)
            payload.update(
                {
                    "text": new_content.strip(),
                    "hash": hashlib.sha256(
                        new_content.strip().encode("utf-8")
                    ).hexdigest(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=memory_id,
                        vector=await self.embedder.embed_query(new_content),
                        payload=payload,
                    )
                ],
            )
        except Exception:
            logger.exception("Long-term memory update failed")

    update_memory = update

    async def delete(self, memory_id: str) -> None:
        if not memory_id:
            return
        try:
            await self._ensure_collection()
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=[memory_id],
            )
        except Exception:
            logger.exception("Long-term memory deletion failed")

    delete_memory = delete

    async def close(self) -> None:
        if hasattr(self.client, "close"):
            await self.client.close()


long_term_memory = LongTermMemory()
