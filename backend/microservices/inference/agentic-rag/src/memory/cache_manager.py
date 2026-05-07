import os
import json
import hashlib
from loguru import logger
from src.core.config import settings
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
class SemanticCache:
    def __init__(self, collection_name="semantic_cache", threshold=0.95):
        self.collection_name = collection_name
        self.threshold = threshold
        qdrant_url = settings.QDRANT_URL
        qdrant_host = settings.QDRANT_HOST
        qdrant_port = settings.QDRANT_PORT
        if qdrant_url:
            self.client = QdrantClient(url=qdrant_url)
        else:
            self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        try:
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            self.emb_dim = self.encoder.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
            self.encoder = None
        self._init_collection()
    def _init_collection(self):
        if not self.encoder:
            return
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.emb_dim, distance=Distance.COSINE),
                )
                logger.info(f"Created semantic cache collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing cache collection: {e}")
    def get_cache(self, prompt: str) -> str:
        if not self.encoder:
            return None
        try:
            query_vector = self.encoder.encode(prompt).tolist()
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=1
            )
            if search_result and search_result[0].score >= self.threshold:
                logger.info(f"Semantic Cache HIT (Score: {search_result[0].score:.4f})")
                return search_result[0].payload.get("response")
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        return None
    def set_cache(self, prompt: str, response: str):
        if not self.encoder:
            return
        try:
            vector = self.encoder.encode(prompt).tolist()
            point_id = hashlib.md5(prompt.encode()).hexdigest()
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "prompt": prompt,
                            "response": response
                        }
                    )
                ]
            )
            logger.debug("Added response to semantic cache.")
        except Exception as e:
            logger.warning(f"Cache insertion error: {e}")
semantic_cache = SemanticCache()
