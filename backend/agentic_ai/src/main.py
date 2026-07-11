from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.database import database
from motor.motor_asyncio import AsyncIOMotorClient
import contextvars
import sys
import uuid
from fastapi import FastAPI, Request
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.core.middleware import add_trace_id_header, trace_id_ctx_var, trace_id_filter
from src.core.metrics import PrometheusMiddleware, metrics_collector, metrics_endpoint
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} {level} [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)
from fastapi.middleware.cors import CORSMiddleware
from src.harness.agentops import agentops
from src.harness.evaluation import evaluation
from src.harness.orchestration import orchestration
from src.api.interaction import router as chat
from src.api.feedback import router as feedback
from src.api.finetuning import router as finetune
from src.api.history import router as history
from src.api.inference import router as inference
from src.api.ingestion import router as ingest
from src.api.events import router as events
from src.api.hill_climbing import router as hill_climbing
from src.api.drm import router as drm_router

app = FastAPI(title="DocLib Agentic AI", version=settings.VERSION)
app.add_middleware(PrometheusMiddleware, service_name="agentic_ai")
app.add_route("/metrics", metrics_endpoint("agentic_ai"))

from fastapi import Request
from fastapi.responses import JSONResponse
@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if "/internal/" in request.url.path:
        token = request.headers.get("X-Internal-Token")
        if token != settings.SECRET_KEY:
            return JSONResponse(status_code=403, content={"detail": "Forbidden invalid internal token"})
    return await call_next(request)

app.middleware("http")(add_trace_id_header)
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.CORS_ALLOWED_ORIGINS.split(",")
        if settings.CORS_ALLOWED_ORIGINS
        else ["*"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(inference)
app.include_router(chat)
app.include_router(ingest)
app.include_router(feedback)
app.include_router(finetune)
app.include_router(history)
app.include_router(events)
app.include_router(hill_climbing)
app.include_router(drm_router)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
@app.get("/evaluate/metrics")
async def harness_metrics():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=agentops.get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )
@app.get("/evaluate/status")
async def harness_status():
    return {
        "orchestration": {
            "active_sessions": orchestration.get_active_sessions(),
            "circuit": orchestration.get_circuit_status(),
        },
        "evaluation": evaluation.get_dashboard_metrics(),
    }
@app.on_event("startup")
async def startup_event():
    logger.info("Agentic AI system initialized successfully")
    from src.store.database import vector_store
    from src.core.infrastructure.configuration import settings
    try:
        await vector_store.ensure_collection()
        logger.info("Qdrant vector store connection established")
    except Exception as e:
        logger.exception("Qdrant vector store initialization error")
    try:
        from src.core.infrastructure.database import init_db
        await init_db()
        if settings.MONGODB_URI:
            from src.core.infrastructure.database import database
            db = database.mongodb[settings.AGENTIC_AI_DB_NAME]
            await db["finetune_datasets"].create_index(
                [("user_id", 1), ("created_at", -1)], background=True
            )
            await db["finetune_samples"].create_index(
                [("dataset_id", 1), ("created_at", 1)], background=True
            )
            await db["finetune_jobs"].create_index(
                [("user_id", 1), ("created_at", -1)], background=True
            )
            await db["finetune_jobs"].create_index(
                [("dataset_id", 1), ("status", 1)], background=True
            )
            logger.info("MongoDB indexing initialized successfully")
    except Exception as e:
        logger.exception("MongoDB indexing error")
    try:
        from src.harness.event_loop import cron_scheduler, event_driven_loop
        await event_driven_loop.start_worker()
        await cron_scheduler.start()
        logger.info("Event-driven loop started successfully")
    except Exception as e:
        logger.exception("Event-driven loop startup error")
@app.on_event("shutdown")
async def shutdown_event():
    try:
        from src.harness.event_loop import cron_scheduler, event_driven_loop
        await cron_scheduler.stop()
        await event_driven_loop.stop_worker()
    except Exception:
        pass
    try:
        from src.core.infrastructure.redis import redis
        await redis.aclose()
    except Exception:
        pass
    try:
        from src.core.infrastructure.mq import mq
        await mq.aclose()
    except Exception:
        pass
