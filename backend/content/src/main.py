from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.bookmark import router as bookmark
from src.api.collaboration import router as collaboration
from src.api.discovery import router as discovery
from src.api.document import router as document
from src.api.highlight import router as highlight
from src.api.library import router as library
from src.api.pin import router as pin
from src.api.publication import router as publication
from src.api.reading import router as reading
from src.api.version import router as version
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.core.infrastructure.database import database
from src.core.infrastructure.redis import redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Content management service provisioned and ready")
    yield
    await close_db()

app = FastAPI(title="DocLib Content", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="content")
app.add_route("/metrics", metrics_endpoint("content"))

from fastapi.responses import JSONResponse

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.CORS_ALLOWED_ORIGINS.split(",")
        if settings.CORS_ALLOWED_ORIGINS
        else []
    ),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(document)
app.include_router(version)
app.include_router(reading)
app.include_router(bookmark)
app.include_router(library)
app.include_router(discovery)
app.include_router(collaboration)
app.include_router(publication)
app.include_router(highlight)
app.include_router(pin)
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "content"}

@app.get("/ready", include_in_schema=False)
async def readiness_check():
    if database.mongodb is None:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    try:
        await database.mongodb.admin.command("ping")
        await redis.ping()
        from src.core.infrastructure.mq import mq

        if not await mq.health_check():
            raise RuntimeError("RabbitMQ is unavailable")
    except Exception:
        logger.exception("Content readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready", "service": "content"}
