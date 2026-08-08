import asyncio
from typing import List
from loguru import logger
from src.services.rag_client import rag_client

class EmbeddingRag:
    def __init__(self):
        self._dimensions = 1024

    async def embed_query(self, query: str) -> List[float]:
        try:
            res = await rag_client.embed_query(query)
            if res:
                return res
        except Exception:
            logger.warning("RAG service embed_query delegation failed")
        return [0.0] * self._dimensions

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            res = await rag_client.embed_batch(texts)
            if res:
                return res
        except Exception:
            logger.warning("RAG service embed_batch delegation failed")
        return [[0.0] * self._dimensions for _ in texts]

embedder = EmbeddingRag()
