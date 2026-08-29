from loguru import logger

from src.knowledge.core.infrastructure.database import close_db, init_db
from src.knowledge.core.infrastructure.redis import redis_client
from src.knowledge.services.embedding import embedder
from src.knowledge.services.retrieval import retriever
from src.knowledge.store.bm25 import bm25_store
from src.knowledge.store.vector import vector_store


async def initialize_knowledge():
    await redis_client.init_redis()
    embedding = await embedder.initialize()
    if len(embedding) != embedder._dimensions:
        raise RuntimeError("Embedding model dimension does not match the knowledge index")
    await vector_store.ensure_collection()
    await bm25_store.initialize(await vector_store.scroll_all())
    await retriever.initialize()
    await init_db()
    logger.info("Veriq knowledge subsystem initialized and ready")


async def shutdown_knowledge():
    await redis_client.close_redis()
    await close_db()
