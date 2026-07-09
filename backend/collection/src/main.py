import asyncio
import contextvars
import sys
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.core.middleware import add_trace_id_header, trace_id_ctx_var, trace_id_filter
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)
logger.add(
    "logs/backend.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
)
from src.api.ingestion import router as collector
from src.core.infrastructure.configuration import settings
app = FastAPI(title="DocLib Crawler", version=settings.VERSION)

from fastapi import Request
from fastapi.responses import JSONResponse
@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if "/internal/" in request.url.path:
        token = request.headers.get("X-Internal-Token")
        if token != settings.SECRET_KEY:
            return JSONResponse(status_code=403, content={"detail": "Forbidden invalid internal token"})
    return await call_next(request)

app.middleware("http")(add_trace_id_header)
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.CORS_ALLOWED_ORIGINS.split(",")
        if settings.CORS_ALLOWED_ORIGINS
        else ["*"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(collector)
@app.on_event("startup")
async def startup_event():
    logger.info("Data collection service is ready")
    from src.core.infrastructure.database import init_db
    await init_db()
    from src.services.queue import run_worker
    asyncio.create_task(run_worker())
@app.get("/health")
async def health_check():
    return {
        "status": "The automated data collection service is currently operating normally and functioning as expected",
        "service": "crawler",
    }
@app.on_event("shutdown")
async def shutdown_event():
    try:
        from src.core.infrastructure.redis import redis
        await redis.aclose()
    except Exception:
        pass
    try:
        from src.core.infrastructure.mq import mq
        await mq.aclose()
    except Exception:
        pass
