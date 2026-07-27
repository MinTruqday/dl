import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.attachment import router as attachment_router
from src.api.conversation import router as conversation_router
from src.api.enhancement import router as enhancement_router
from src.api.group import router as group_router
from src.api.interaction import router as interaction_router
from src.api.pin import router as pin_router
from src.api.privacy import router as privacy_router
from src.api.thread import router as thread_router
from src.core.http import ai_http_client
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db
from src.core.infrastructure.redis import redis
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.services.thread import ThreadService


async def scheduled_message_worker():
    while True:
        try:
            await ThreadService.process_scheduled_messages()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduled message worker failed")
        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    worker = asyncio.create_task(scheduled_message_worker())
    logger.info("Messaging service initialized")
    try:
        yield
    finally:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker
        await ai_http_client.aclose()
        await redis.aclose()
        await close_db()


app = FastAPI(title="DocLib Messaging", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="messaging")
app.add_route("/metrics", metrics_endpoint("messaging"))
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
app.include_router(conversation_router)
app.include_router(thread_router)
app.include_router(group_router)
app.include_router(interaction_router)
app.include_router(pin_router)
app.include_router(privacy_router)
app.include_router(attachment_router)
app.include_router(enhancement_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check():
    checks = {}
    try:
        await database.mongodb.admin.command("ping")
        checks["mongodb"] = "ready"
    except Exception:
        checks["mongodb"] = "unavailable"
    try:
        checks["redis"] = "ready" if await redis.get_client().ping() else "unavailable"
    except Exception:
        checks["redis"] = "unavailable"
    ready = all(value == "ready" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "degraded", "checks": checks},
    )
