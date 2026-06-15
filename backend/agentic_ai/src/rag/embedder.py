import asyncio
from typing import List
import httpx
from core.config import settings
from loguru import logger

class EmbeddingService:
    def __init__(self):
        self._model = settings.EMBEDDING_MODEL
        self._dimensions = settings.EMBEDDING_DIMENSIONS
        self._batch_size = settings.EMBEDDING_BATCH_SIZE
        self._url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self._model}"
        self._headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
        self._client = httpx.AsyncClient(timeout=60.0)

    async def embed_query(self, text: str) -> List[float]:
        try:
            response = await self._client.post(self._url, headers=self._headers, json={"inputs": [text]})
            if response.status_code == 200:
                return response.json()[0]
            logger.error("The semantic embedding generative model forcefully rejected incoming specific text encoding request")
            return [0.0] * self._dimensions
        except Exception:
            logger.error("The systematic artificial intelligence framework failed retrieving dimensional vector representations correctly")
            return [0.0] * self._dimensions

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            try:
                response = await self._client.post(self._url, headers=self._headers, json={"inputs": batch})
                if response.status_code == 200:
                    embeddings.extend(response.json())
                else:
                    embeddings.extend([[0.0] * self._dimensions for _ in batch])
            except Exception:
                logger.error("The semantic contextual indexing mechanism collapsed translating text blocks into vector matrices")
                embeddings.extend([[0.0] * self._dimensions for _ in batch])
            await asyncio.sleep(0.1)
        return embeddings

embedding_service = EmbeddingService()