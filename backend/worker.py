import asyncio
import logging
from config.settings import settings
from core.database import db_client
from services.rag import RagService
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

async def cleanup_orphaned_document(document_id: str):
    logger.info(f"Worker received cleanup event for document: {document_id}")
    try:
        logger.info(f"Removing vectors from VectorDB for document: {document_id}")
        
        logger.info(f"Removing physical files from object storage for document: {document_id}")
        
        logger.info(f"Successfully cleaned up orphaned data for document {document_id}")
    except Exception as e:
        logger.error(f"Failed to cleanup orphaned data for document {document_id}: {e}")

async def redis_listener():
    await db_client.connect()
    
    if not hasattr(db_client, 'redis') or not db_client.redis:
        logger.error("Redis client is not initialized. Worker cannot start.")
        return
        
    pubsub = db_client.redis.pubsub()
    await pubsub.subscribe("DocumentDeleted")
    
    logger.info("Worker started, listening to DocumentDeleted channel...")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                document_id = message["data"].decode("utf-8")
                asyncio.create_task(cleanup_orphaned_document(document_id))
    except asyncio.CancelledError:
        logger.info("Worker stopped.")
    finally:
        await pubsub.unsubscribe("DocumentDeleted")
        await db_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(redis_listener())
    except KeyboardInterrupt:
        logger.info("Worker shutting down.")
