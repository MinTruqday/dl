from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from src.core.infrastructure.configuration import settings
from src.api.redis_api import router as redis_router
from src.api.redis_api import get_redis

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
)

app = FastAPI(title="DocLib Cache", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(redis_router)

@app.on_event("startup")
async def startup_event():
    await get_redis()
    logger.info("Cache Service đã sẵn sàng")

@app.get("/health")
async def health_check():
    return {
        "status": "Cache service is healthy"
    }



@app.on_event("shutdown")
async def shutdown_event():
    try:
        from src.core.infrastructure.redis_client import redis_client
        await redis_client.aclose()
    except Exception:
        pass
    try:
        from src.core.infrastructure.mq import mq
        await mq.aclose()
    except Exception:
        pass
