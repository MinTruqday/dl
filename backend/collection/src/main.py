import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.ingestion import router as collector
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db
from src.core.infrastructure.mq import mq
from src.core.infrastructure.redis import redis
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.core.middleware import add_trace_id_header, trace_id_filter
from src.core.storage import storage
from src.services.queue import start_workers, stop_workers


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await storage._ensure_bucket()
    await start_workers()
    logger.info("Data collection service is ready")
    try:
        yield
    finally:
        await stop_workers()
        await storage.aclose()
        await close_db()


app = FastAPI(title="DocLib Collection", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="collection")
app.add_route("/metrics", metrics_endpoint("collection"))
app.middleware("http")(add_trace_id_header)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(collector)


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "collection"}


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    try:
        if database.mongodb is None:
            raise RuntimeError("MongoDB is not initialized")
        await database.mongodb.admin.command("ping")
        await redis.ping()
        if not await mq.health_check():
            raise RuntimeError("RabbitMQ is unavailable")
        await storage.health_check()
    except Exception:
        logger.exception("Collection readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready", "service": "collection"}
