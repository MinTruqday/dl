import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.composition import router as composition_router
from src.api.editorjs import router as editorjs_router
from src.api.latex import router as latex_router
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db
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
    await init_db()
    logger.info("Document compilation service initialized")
    try:
        yield
    finally:
        await close_db()


app = FastAPI(title="DocLib Compilation", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="compilation")
app.add_route("/metrics", metrics_endpoint("compilation"))
app.middleware("http")(add_trace_id_header)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(latex_router)
app.include_router(editorjs_router)
app.include_router(composition_router)


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "compilation"}


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    try:
        if database.mongodb is None:
            raise RuntimeError("MongoDB is not initialized")
        await database.mongodb.admin.command("ping")
        await redis.ping()
    except Exception:
        logger.exception("Compilation readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready", "service": "compilation"}
