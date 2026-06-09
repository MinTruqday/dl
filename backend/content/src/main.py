from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

from src.api.document import router as document_router
from src.api.editor import router as editor_router
from src.api.version import router as version_router
from src.api.collaboration import router as collaboration_router
from src.api.highlight import router as highlight_router
from src.api.pin import router as pin_router
from src.api.bookmark import router as bookmark_router
from src.api.reading import router as reading_router
from src.api.export import router as export_router
from src.api.upload import router as upload_router
from src.api.storage import router as storage_router
from src.api.publication import router as publication_router
from src.api.library import router as library_router
from src.api.discovery import router as discovery_router
from src.api.review import router as review_router
from src.api.quota import router as quota_router
from src.api.draft import router as draft_router

app = FastAPI(title="DocLib Content")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_router)
app.include_router(editor_router)
app.include_router(version_router)
app.include_router(collaboration_router)
app.include_router(highlight_router)
app.include_router(pin_router)
app.include_router(bookmark_router)
app.include_router(reading_router)
app.include_router(export_router)
app.include_router(upload_router)
app.include_router(storage_router)
app.include_router(publication_router)
app.include_router(library_router)
app.include_router(discovery_router)
app.include_router(review_router)
app.include_router(quota_router)
app.include_router(draft_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting DocLib Content")
    from src.core.database import db_client
    from src.core.config import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    import redis.asyncio as aioredis
    db_client.mongodb = AsyncIOMotorClient(settings.MONGODB_URI)
    try:
        db_client.redis = await aioredis.from_url(settings.REDIS_URI, decode_responses=True)
        logger.info("Connected to Redis")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        db_client.redis = None


@app.on_event("shutdown")
async def shutdown_event():
    from src.core.database import db_client
    if db_client.mongodb:
        db_client.mongodb.close()
    if db_client.redis:
        await db_client.redis.close()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "DocLib Content"}
