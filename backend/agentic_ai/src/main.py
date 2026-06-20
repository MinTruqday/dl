import contextvars
import sys
import uuid

from core.middleware import add_trace_id_header, trace_id_ctx_var, trace_id_filter
from core.repositories.base_repository import RepositoryFactory
from fastapi import FastAPI, Request
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} {level} [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)
from src.router.chat_router import router as chat_router
from src.router.feedback_router import router as feedback_router
from src.router.finetune_router import router as finetune_router
from src.router.history_router import router as history_router
from src.router.inference_router import router as inference_router
from src.router.ingest_router import router as ingest_router
from fastapi.middleware.cors import CORSMiddleware
from src.harness.agentops_harness import agentops_harness
from src.harness.evaluation_harness import evaluation_harness
from src.harness.orchestration_harness import orchestration_harness

app = FastAPI(title="DocLib Agentic AI", version=settings.VERSION)
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

app.include_router(inference_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(feedback_router)
app.include_router(finetune_router)
app.include_router(history_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/evaluate/metrics")
async def harness_metrics():
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(
        content=agentops_harness.get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )


@app.get("/evaluate/status")
async def harness_status():
    return {
        "orchestration": {
            "active_sessions": orchestration_harness.get_active_sessions(),
            "circuit_breaker": orchestration_harness.get_circuit_status(),
        },
        "evaluation": evaluation_harness.get_dashboard_metrics(),
    }


@app.on_event("startup")
async def startup_event():
    logger.info("Khởi tạo AI thành công")
    from core.config import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    from src.store.vector_store import vector_store

    try:
        await vector_store.ensure_collection()
        logger.info("Khởi tạo cơ sở dữ liệu vector thành công")
    except Exception:
        logger.error("Lỗi khởi tạo cơ sở dữ liệu vector")

    try:
        if settings.MONGODB_URI:
            client = AsyncIOMotorClient(settings.MONGODB_URI)
            db = client.get_default_database()
            await RepositoryFactory.get("finetune_datasets").create_index(
                [("user_id", 1), ("created_at", -1)], background=True
            )
            await RepositoryFactory.get("finetune_samples").create_index(
                [("dataset_id", 1), ("created_at", 1)], background=True
            )
            await RepositoryFactory.get("finetune_jobs").create_index(
                [("user_id", 1), ("created_at", -1)], background=True
            )
            await RepositoryFactory.get("finetune_jobs").create_index(
                [("dataset_id", 1), ("status", 1)], background=True
            )
            logger.info("Khởi tạo chỉ mục cơ sở dữ liệu thành công")
    except Exception:
        logger.error("Lỗi khởi tạo chỉ mục cơ sở dữ liệu")