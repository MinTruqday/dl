import sys
import hmac
import re
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.middleware import add_trace_id_header, trace_id_filter
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.core.dependency import Role, require_role
logger.remove()

def _safe_log_sink(message):
    from src.core.security.guardrails import guardrails_engine

    result = guardrails_engine.inspect_output(str(message))
    sys.stdout.write(result.get("sanitized_text", str(message)))

logger.add(
    _safe_log_sink,
    format="{time:YYYY-MM-DD HH:mm:ss} {level} [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
    backtrace=False,
    diagnose=False,
)
from fastapi.middleware.cors import CORSMiddleware
from src.harness.agentops import agentops
from src.loop.evaluation import evaluation
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
from src.api.mcp import router as mcp_router
from src.api.interrupt import router as interrupt_router

app = FastAPI(title="DocLib Agentic AI", version=settings.VERSION)
app.add_middleware(PrometheusMiddleware, service_name="agentic_ai")
app.add_route("/metrics", metrics_endpoint("agentic_ai"))

from fastapi.responses import JSONResponse
@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if "/internal/" in request.url.path:
        token = request.headers.get("X-Internal-Token")
        if not token or not settings.SECRET_KEY or not hmac.compare_digest(token, settings.SECRET_KEY):
            return JSONResponse(status_code=403, content={"detail": {"code": "invalid_internal_token"}})
    return await call_next(request)

app.middleware("http")(add_trace_id_header)
allowed_origins = (
    settings.CORS_ALLOWED_ORIGINS.split(",")
    if settings.CORS_ALLOWED_ORIGINS
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials="*" not in allowed_origins,
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
app.include_router(mcp_router)
app.include_router(interrupt_router)
@app.get("/health")
async def health_check():
    """Report process liveness for container health monitoring"""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Report readiness of every infrastructure dependency required for requests"""
    checks = {}
    try:
        await database.mongodb.admin.command("ping")
        checks["mongodb"] = "ready"
    except Exception:
        checks["mongodb"] = "unavailable"
    try:
        from src.core.infrastructure.redis import redis
        checks["redis"] = "ready" if await redis.get_client().ping() else "unavailable"
    except Exception:
        checks["redis"] = "unavailable"
    try:
        from src.core.infrastructure.mq import mq
        checks["rabbitmq"] = "ready" if await mq.health_check() else "unavailable"
    except Exception:
        checks["rabbitmq"] = "unavailable"
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{settings.QDRANT_URL.rstrip('/')}/collections")
        checks["qdrant"] = "ready" if response.status_code == 200 else "unavailable"
    except Exception:
        checks["qdrant"] = "unavailable"
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{settings.RAG_URL}/ready")
        checks["rag"] = "ready" if response.status_code == 200 else "unavailable"
    except Exception:
        checks["rag"] = "unavailable"
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(
                f"{settings.MINIO_ENDPOINT.rstrip('/')}/minio/health/ready"
            )
            checks["object_storage"] = (
                "ready" if response.status_code == 200 else "unavailable"
            )
    except Exception:
        checks["object_storage"] = "unavailable"
    try:
        from src.utils.local_models import local_model_client

        checks.update(await local_model_client.readiness())
    except Exception:
        checks["model"] = "unavailable"
    required_checks = {
        key: value
        for key, value in checks.items()
        if key != "model"
    }
    infrastructure_ready = all(
        value == "ready" for value in required_checks.values()
    )
    model_ready = checks.get("model") == "ready"
    ready = infrastructure_ready and model_ready
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "degraded", "checks": checks},
    )
@app.get("/evaluate/metrics")
async def harness_metrics():
    """Expose agent harness telemetry in Prometheus text format"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=agentops.get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )
@app.get(
    "/evaluate/status",
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def harness_status():
    """Return orchestration circuit and evaluation status for administrators"""
    return {
        "orchestration": {
            "active_sessions": orchestration.get_active_sessions(),
            "circuit": orchestration.get_circuit_status(),
        },
        "evaluation": evaluation.get_dashboard_metrics(),
    }
async def startup_event():
    logger.info("Agentic AI system initialized")
    from src.core.infrastructure.configuration import settings
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
            logger.info("MongoDB indexing initialized")
    except Exception:
        logger.exception("MongoDB indexing error")
    try:
        from src.loop.event import cron_scheduler, event_driven_loop
        await event_driven_loop.start_worker()
        await cron_scheduler.start()
        logger.info("Event-driven loop started")
    except Exception:
        logger.exception("Event-driven loop startup error")
    try:
        from src.utils.background import create_background_task
        from src.utils.local_models import local_model_client

        create_background_task(
            local_model_client.warm_primary(),
            "primary-model-warmup",
        )
    except Exception:
        logger.exception("Primary model warmup startup error")
async def shutdown_event():
    try:
        from src.utils.background import drain_background_tasks

        await drain_background_tasks()
    except Exception:
        logger.exception("Background task shutdown failed")
    try:
        from src.loop.event import cron_scheduler, event_driven_loop
        await cron_scheduler.stop()
        await event_driven_loop.stop_worker()
    except Exception:
        logger.exception("Event loop shutdown failed")
    try:
        from src.core.infrastructure.redis import redis
        await redis.aclose()
    except Exception:
        logger.exception("Redis shutdown failed")
    try:
        from src.core.infrastructure.mq import mq
        await mq.aclose()
    except Exception:
        logger.exception("Message queue shutdown failed")
    try:
        from src.core.infrastructure.database import close_db
        await close_db()
    except Exception:
        logger.exception("Database shutdown failed")
    try:
        from src.memory.management import memory_manager
        await memory_manager.close()
        if memory_manager._redis:
            await memory_manager._redis.aclose()
    except Exception:
        logger.exception("Memory manager shutdown failed")
    try:
        from src.workflow.orchestration import supervisor
        supervisor.checkpointer.close()
        supervisor.sync_client.close()
    except Exception:
        logger.exception("Workflow checkpointer shutdown failed")

@asynccontextmanager
async def lifespan(application: FastAPI):
    await startup_event()
    try:
        yield
    finally:
        await shutdown_event()

app.router.lifespan_context = lifespan
