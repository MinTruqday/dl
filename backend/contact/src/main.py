import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

from src.api.message import router as message_router

app = FastAPI(title="DocLib Contact")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(message_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting DocLib Contact")
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
    return {"status": "ok", "service": "DocLib Contact"}
