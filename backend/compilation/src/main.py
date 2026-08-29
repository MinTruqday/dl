import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.redis import redis
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.core.middleware import add_trace_id_header, trace_id_filter


logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis.ping()
    logger.info("Document compilation service initialized")
    try:
        yield
    finally:
        await redis.aclose()


app = FastAPI(title="Veriq Compilation", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="compilation")
app.add_route("/metrics", metrics_endpoint("compilation"))
app.middleware("http")(add_trace_id_header)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "compilation"}


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    try:
        await redis.ping()
    except Exception:
        logger.exception("Compilation readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready", "service": "compilation"}
