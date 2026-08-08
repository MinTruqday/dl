from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from src.api.reading import router as reading_router
from src.api.highlight import router as highlight_router
from src.api.bookmark import router as bookmark_router
from src.api.pin import router as pin_router
from src.api.discovery import router as discovery_router
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db
from src.core.infrastructure.redis import redis
from src.core.metrics import PrometheusMiddleware, metrics_endpoint

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Engagement service provisioned and ready")
    try:
        yield
    finally:
        await redis.aclose()
        await close_db()

app = FastAPI(title="DocLib Engagement", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="engagement")
app.add_route("/metrics", metrics_endpoint("engagement"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        if settings.CORS_ALLOWED_ORIGINS
        else ["*"]
    ),
    allow_credentials=bool(settings.CORS_ALLOWED_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reading_router)
app.include_router(highlight_router)
app.include_router(bookmark_router)
app.include_router(pin_router)
app.include_router(discovery_router)

@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "engagement"}

@app.get("/ready", include_in_schema=False)
async def readiness_check():
    checks = {}
    try:
        if database.mongodb is not None:
            await database.mongodb.command("ping")
            checks["mongodb"] = "ready"
        else:
            checks["mongodb"] = "unavailable"
    except Exception:
        checks["mongodb"] = "unavailable"
    try:
        checks["redis"] = "ready" if await redis.get_client().ping() else "unavailable"
    except Exception:
        checks["redis"] = "unavailable"
    ready = all(value == "ready" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "degraded", "checks": checks, "service": "engagement"},
    )
