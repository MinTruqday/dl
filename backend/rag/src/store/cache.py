import math
from typing import Dict, List, Optional
from loguru import logger

class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.90, ttl_seconds: int = 86400):
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self._memory_cache: Dict[str, Dict] = {}

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    async def get(self, query_text: str, query_vector: Optional[List[float]] = None) -> Optional[str]:
        if not query_text:
            return None

        if query_vector:
            best_score = 0.0
            best_response = None
            for key, item in list(self._memory_cache.items()):
                cached_vec = item.get("vector")
                if cached_vec:
                    score = self._cosine_similarity(query_vector, cached_vec)
                    if score > best_score:
                        best_score = score
                        best_response = item.get("response")

            if best_score >= self.similarity_threshold and best_response:
                logger.info(f"Semantic cache hit with similarity score {best_score:.4f}")
                return best_response

        for key, item in list(self._memory_cache.items()):
            if item.get("query") == query_text:
                logger.info("Exact semantic cache hit")
                return item.get("response")

        return None

    async def set(self, query_text: str, response_text: str, query_vector: Optional[List[float]] = None):
        if not query_text or not response_text:
            return

        cache_entry = {
            "query": query_text,
            "response": response_text,
            "vector": query_vector
        }
        self._memory_cache[query_text] = cache_entry
        logger.info("Saved query and response to semantic cache")

semantic_cache = SemanticCache()
