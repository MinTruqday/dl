import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.deposit import router as deposit_router
from src.api.monetization import router as monetization_router
from src.api.transfer import router as transfer_router
from src.api.wallet import router as wallet_router
from src.api.withdrawal import router as withdrawal_router
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db
from src.core.infrastructure.redis import redis
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.outbox_worker import process_outbox
from src.services.transfer import TransferService


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await redis.get_client().ping()
    outbox_task = asyncio.create_task(process_outbox())
    transfer_task = asyncio.create_task(TransferService.recover_pending_transfers())
    logger.info("Finance service initialized")
    try:
        yield
    finally:
        outbox_task.cancel()
        transfer_task.cancel()
        try:
            await outbox_task
        except asyncio.CancelledError:
            pass
        try:
            await transfer_task
        except asyncio.CancelledError:
            pass
        await redis.aclose()
        await close_db()


app = FastAPI(title="DocLib Finance", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="finance")
app.add_route("/metrics", metrics_endpoint("finance"))
origins = [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=bool(origins),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(wallet_router)
app.include_router(deposit_router)
app.include_router(withdrawal_router)
app.include_router(monetization_router)
app.include_router(transfer_router)


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
