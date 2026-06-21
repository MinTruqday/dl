import asyncio
import hashlib
import json
import os
from typing import List

import redis
from loguru import logger
from sentence_transformers import SentenceTransformer

from core.infrastructure.app_config import settings


class VectorEmbedding:
    def __init__(self):
        self._model_name = settings.EMBEDDING_MODEL
        self._dimensions = settings.EMBEDDING_DIMENSIONS
        self._batch_size = settings.EMBEDDING_BATCH_SIZE
        self._model = SentenceTransformer(self._model_name)

        redis_url = settings.REDIS_URI
        try:
            self._cache = redis.from_url(redis_url, decode_responses=False)
            self._cache.ping()
        except Exception:
            self._cache = None

    def _cache_key(self, text: str) -> str:
        return f"emb:local:{self._model_name}:{hashlib.sha256(text.encode()).hexdigest()[:24]}"

    def _embed_single(self, text: str) -> List[float]:
        if self._cache:
            cached = self._cache.get(self._cache_key(text))
            if cached:
                return json.loads(cached)

        embedding = self._model.encode(text, convert_to_numpy=True).tolist()

        if self._cache:
            self._cache.setex(self._cache_key(text), 86400 * 7, json.dumps(embedding))

        return embedding

    async def embed_query(self, query: str) -> List[float]:
        return await asyncio.to_thread(self._embed_single, query)

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        all_embeddings = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            if self._cache:
                cached = self._cache.get(self._cache_key(text))
                if cached:
                    all_embeddings[i] = json.loads(cached)
                    continue
            uncached_indices.append(i)
            uncached_texts.append(text)

        if uncached_texts:
            for batch_start in range(0, len(uncached_texts), self._batch_size):
                batch = uncached_texts[batch_start : batch_start + self._batch_size]
                batch_embeddings = self._model.encode(batch, convert_to_numpy=True)

                for j, emb in enumerate(batch_embeddings):
                    real_idx = uncached_indices[batch_start + j]
                    emb_list = emb.tolist()
                    all_embeddings[real_idx] = emb_list
                    if self._cache:
                        self._cache.setex(
                            self._cache_key(batch[j]), 86400 * 7, json.dumps(emb_list)
                        )

        return all_embeddings

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return await asyncio.to_thread(self._embed_batch, texts)


embedder = VectorEmbedding()
