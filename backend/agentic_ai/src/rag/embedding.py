from typing import List
from src.services.rag_client import rag_client

class EmbeddingRag:
    def __init__(self):
        self._dimensions = 1024

    async def embed_query(self, query: str) -> List[float]:
        embedding = await rag_client.embed_query(query)
        if len(embedding) != self._dimensions:
            raise RuntimeError("RAG embedding dimension mismatch")
        return embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = await rag_client.embed_batch(texts)
        if len(embeddings) != len(texts) or any(
            len(embedding) != self._dimensions for embedding in embeddings
        ):
            raise RuntimeError("RAG batch embedding dimension mismatch")
        return embeddings

embedder = EmbeddingRag()
