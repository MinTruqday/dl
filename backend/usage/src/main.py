from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
from fastapi import Request
from fastapi.responses import JSONResponse
from src.core.infrastructure.database import database
from src.core.infrastructure.redis import redis

from src.api.tier import router as tier_router
from src.api.quota import router as quota_router
from src.core.metrics import PrometheusMiddleware, metrics_collector, metrics_endpoint

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Usage management service provisioned and ready")
    yield
    logger.info("Usage management service shutting down")
    await close_db()

app = FastAPI(title="DocLib Usage", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="usage")
app.add_route("/metrics", metrics_endpoint("usage"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "healthy", "service": "usage"}

@app.get("/ready", include_in_schema=False)
async def ready():
    if database.mongodb is None:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    try:
        await database.mongodb.admin.command("ping")
        await redis.ping()
    except Exception:
        logger.exception("Usage readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready", "service": "usage"}

app.include_router(tier_router)
app.include_router(quota_router)
