from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from loguru import logger
from src.api.document import router as document_router
from src.api.cloud import router as cloud_router
from src.api.smart import router as smart_router
from src.api.preview import router as preview_router
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db
from src.core.infrastructure.redis import redis
from src.core.metrics import PrometheusMiddleware, metrics_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Search service provisioned and ready")
    try:
        yield
    finally:
        await redis.aclose()
        await close_db()


app = FastAPI(title="DocLib Search", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="search")
app.add_route("/metrics", metrics_endpoint("search"))
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

app.include_router(document_router, prefix="/tim-kiem")
app.include_router(cloud_router, prefix="/tim-kiem")
app.include_router(smart_router, prefix="/tim-kiem")
app.include_router(preview_router, prefix="/tim-kiem")


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "search"}


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
    for dependency, url in {
        "content": settings.CONTENT_URL,
        "cloud": settings.CLOUD_URL,
    }.items():
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{url}/ready")
            checks[dependency] = "ready" if response.status_code == 200 else "unavailable"
        except Exception:
            checks[dependency] = "unavailable"
    ready = all(value == "ready" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "degraded", "checks": checks, "service": "search"},
    )
