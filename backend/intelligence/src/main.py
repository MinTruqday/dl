import contextvars
import sys
import uuid

from fastapi import FastAPI, Request
from loguru import logger
from shared.infrastructure.config import settings

from shared.middlewares import add_trace_id_header, trace_id_ctx_var, trace_id_filter
from shared.repositories.base_repository import RepositoryFactory

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} {level} [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)
from fastapi.middleware.cors import CORSMiddleware
from src.harness.agent_ops import agentops
from src.harness.models_evaluations import evaluation
from src.harness.agent_orchestrators import orchestration
from src.api.chat_interactions import router as chat
from src.api.user_feedback import router as feedback
from src.api.models_finetuning_jobs import router as finetune
from src.api.session_histories import router as history
from src.api.models_inference import router as inference
from src.api.data_ingestion import router as ingest

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

app.include_router(inference)
app.include_router(chat)
app.include_router(ingest)
app.include_router(feedback)
app.include_router(finetune)
app.include_router(history)


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
            "circuit_breaker": orchestration.get_circuit_status(),
        },
        "evaluation": evaluation.get_dashboard_metrics(),
    }


@app.on_event("startup")
async def startup_event():
    logger.info("Khởi tạo AI thành công")
    from motor.motor_asyncio import AsyncIOMotorClient
    from src.store.vector_database import vector_store

    from shared.infrastructure.config import settings

    try:
        await vector_store.ensure_collection()
        logger.info("Khởi tạo cơ sở dữ liệu vector thành công")
    except Exception:
        logger.error("Lỗi khởi tạo cơ sở dữ liệu vector")

    try:
        if settings.MONGODB_URI:
            client = AsyncIOMotorClient(settings.MONGODB_URI)
            db = client.get_default_database()
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
            logger.info("Khởi tạo chỉ mục cơ sở dữ liệu thành công")
    except Exception as e:
        logger.exception(f"Lỗi khởi tạo chỉ mục cơ sở dữ liệu: {str(e)}")
