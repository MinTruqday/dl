from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.audit import router as audit
from src.api.health import router as operation
from src.api.telemetry import router as telemetry
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.core.infrastructure.database import database
from src.core.infrastructure.redis import redis
from src.core.storage import close_storage_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Management service provisioned and ready")
    yield
    await close_storage_client()
    await close_db()

app = FastAPI(title="DocLib Management", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="management")
app.add_route("/metrics", metrics_endpoint("management"))

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
app.include_router(audit)
app.include_router(telemetry)
app.include_router(operation)
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "management"}

@app.get("/ready", include_in_schema=False)
async def readiness_check():
    if database.mongodb is None:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    try:
        await database.mongodb.admin.command("ping")
        await redis.ping()
        from src.core.storage import get_storage_client

        storage = await get_storage_client()
        await storage.head_bucket(Bucket=settings.MINIO_PRIVATE_BUCKET)
    except Exception:
        logger.exception("Management readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready", "service": "management"}
