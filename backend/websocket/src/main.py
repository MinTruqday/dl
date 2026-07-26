from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.composition import router as composition_socket
from src.api.message import router as message_socket
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.sockets.composition import composition_socket_manager
from src.sockets.message import message_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await composition_socket_manager.start()
    await message_manager.start()
    logger.info("WebSocket service initialized successfully")
    try:
        yield
    finally:
        await composition_socket_manager.close()
        await message_manager.close()
        await close_db()


app = FastAPI(
    title="DocLib WebSocket",
    version=settings.VERSION,
    lifespan=lifespan,
)
app.add_middleware(PrometheusMiddleware, service_name="websocket")
app.add_route("/metrics", metrics_endpoint("websocket"))
origins = [
    origin.strip()
    for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=bool(origins),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(composition_socket)
app.include_router(message_socket)


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "websocket"}


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    checks = {}
    try:
        await database.mongodb.admin.command("ping")
        checks["mongodb"] = "ready"
    except Exception:
        checks["mongodb"] = "unavailable"
    try:
        checks["redis"] = "ready" if await database.redis.ping() else "unavailable"
    except Exception:
        checks["redis"] = "unavailable"
    checks["composition_listener"] = (
        "ready" if composition_socket_manager.is_running() else "unavailable"
    )
    checks["message_listener"] = (
        "ready" if message_manager.is_running() else "unavailable"
    )
    ready = all(value == "ready" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "degraded",
            "service": "websocket",
            "checks": checks,
        },
    )
