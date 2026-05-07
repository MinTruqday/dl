import os
from loguru import logger
from typing import List
import hashlib
import json
import redis
from sentence_transformers import SentenceTransformer
from src.core.config import settings
class EmbeddingService:
    def __init__(self):
        self._model_name = settings.EMBEDDING_MODEL
        self._dimensions = settings.EMBEDDING_DIMENSIONS
        self._batch_size = settings.EMBEDDING_BATCH_SIZE
logger.info("Log message sanitized"))
        self._model = SentenceTransformer(self._model_name)
logger.info("Log message sanitized"))
        redis_url = settings.REDIS_URI
        try:
            self._cache = redis.from_url(redis_url, decode_responses=False)
            self._cache.ping()
        except Exception:
            self._cache = None
logger.info("Log message sanitized"))
    def _cache_key(self, text: str) -> str:
        return f"emb:local:{self._model_name}:{hashlib.sha256(text.encode()).hexdigest()[:24]}"
    def embed_single(self, text: str) -> List[float]:
        model_text = text
        if self._cache:
            cached = self._cache.get(self._cache_key(model_text))
            if cached:
                return json.loads(cached)
        embedding = self._model.encode(model_text, convert_to_numpy=True).tolist()
        if self._cache:
            self._cache.setex(
                self._cache_key(model_text),
                86400 * 7,
                json.dumps(embedding)
            )
        return embedding
    def embed_query(self, query: str) -> List[float]:
        return self.embed_single(query)
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        all_embeddings = []
        uncached_indices = []
        uncached_texts = []
        for i, text in enumerate(texts):
            model_text = text
            if self._cache:
                cached = self._cache.get(self._cache_key(model_text))
                if cached:
                    all_embeddings.append(json.loads(cached))
                    continue
            uncached_indices.append(i)
            uncached_texts.append(model_text)
            all_embeddings.append(None)
        if uncached_texts:
            for batch_start in range(0, len(uncached_texts), self._batch_size):
                batch = uncached_texts[batch_start:batch_start + self._batch_size]
                batch_embeddings = self._model.encode(batch, convert_to_numpy=True)
                for j, emb in enumerate(batch_embeddings):
                    real_idx = uncached_indices[batch_start + j]
                    emb_list = emb.tolist()
                    all_embeddings[real_idx] = emb_list
                    if self._cache:
                        self._cache.setex(
                            self._cache_key(batch[j]),
                            86400 * 7,
                            json.dumps(emb_list)
                        )
logger.info("Log message sanitized"))
        return all_embeddings
embedding_service = EmbeddingService()
