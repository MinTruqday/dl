from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
import asyncio
from src.core.config import settings
from src.sockets.router import router as socket_router
from src.sockets.chat_manager import chat_manager

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

app = FastAPI(title="DocLib WebSocket")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(socket_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting WebSocket Service")
    import redis.asyncio as aioredis
    try:
        chat_manager.redis_client = await aioredis.from_url(settings.REDIS_URI, decode_responses=True)
        logger.info("Connected to Redis")
        asyncio.create_task(chat_manager.listen_redis())
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    if chat_manager.pubsub:
        await chat_manager.pubsub.unsubscribe("chat_channel")
    if chat_manager.redis_client:
        await chat_manager.redis_client.close()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "DocLib WebSocket"}
