from typing import List, Optional
from src.store.cache import semantic_cache
from src.services.embedding import embedder
from src.schemas.cache import CacheGetResponse


class CacheService:
    async def get_response(
        self, query_text: str, query_vector: Optional[List[float]] = None
    ) -> CacheGetResponse:
        if not query_vector:
            query_vector = await embedder.embed_query(query_text)
        cached = await semantic_cache.get(query_text, query_vector)
        if cached:
            return CacheGetResponse(hit=True, response=cached)
        return CacheGetResponse(hit=False, response=None)

    async def set_response(
        self, query_text: str, response_text: str, query_vector: Optional[List[float]] = None
    ) -> None:
        if not query_vector:
            query_vector = await embedder.embed_query(query_text)
        await semantic_cache.set(query_text, response_text, query_vector)


cache_service = CacheService()
