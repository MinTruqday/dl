from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from loguru import logger
from src.api.invite import router as invite_router
from src.api.member import router as member_router
from src.api.link import router as link_router
from src.api.access_request import router as access_request_router
from src.api.presence import router as presence_router
from src.api.activity import router as activity_router
from src.api.task import router as task_router
from src.api.memo import router as memo_router
from src.api.lock import router as lock_router
from src.api.snapshot import router as snapshot_router
from src.api.internal import router as internal_router
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db
from src.core.infrastructure.redis import redis
from src.core.metrics import PrometheusMiddleware, metrics_endpoint

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Collaboration service provisioned and ready")
    try:
        yield
    finally:
        await redis.aclose()
        await close_db()

app = FastAPI(title="DocLib Collaboration", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="collaboration")
app.add_route("/metrics", metrics_endpoint("collaboration"))
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

app.include_router(invite_router)
app.include_router(member_router)
app.include_router(link_router)
app.include_router(access_request_router)
app.include_router(presence_router)
app.include_router(activity_router)
app.include_router(task_router)
app.include_router(memo_router)
app.include_router(lock_router)
app.include_router(snapshot_router)
app.include_router(internal_router)

@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "collaboration"}

@app.get("/ready", include_in_schema=False)
async def readiness_check():
    checks = {}
    try:
        if database.mongodb is not None:
            await database.mongodb.admin.command("ping")
            checks["mongodb"] = "ready"
        else:
            checks["mongodb"] = "unavailable"
    except Exception:
        checks["mongodb"] = "unavailable"
    try:
        checks["redis"] = "ready" if await redis.get_client().ping() else "unavailable"
    except Exception:
        checks["redis"] = "unavailable"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.CONTENT_URL}/ready")
        checks["content"] = "ready" if response.status_code == 200 else "unavailable"
    except Exception:
        checks["content"] = "unavailable"
    ready = all(value == "ready" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "degraded", "checks": checks, "service": "collaboration"},
    )
