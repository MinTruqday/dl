from core.middleware import trace_id_ctx_var, trace_id_filter, add_trace_id_header
from fastapi import FastAPI, Request
from loguru import logger
import uuid
import contextvars
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} {level} [{extra[trace_id]}] {message}", filter=trace_id_filter, level="INFO")
from src.api.inference import router as inference_router
from src.api.chat import router as chat_router
from src.api.ingest import router as ingest_router
from src.api.feedback import router as feedback_router
from src.api.finetune import router as finetune_router
from src.api.history import router as history_router
from src.harness.agentops_harness import agentops_harness
from src.harness.orchestration_harness import orchestration_harness
from src.harness.evaluation_harness import evaluation_harness

app = FastAPI(title="DocLib Agentic_ai")
app.middleware("http")(add_trace_id_header)

app.include_router(inference_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(feedback_router)
app.include_router(finetune_router)
app.include_router(history_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/harness/metrics")
async def harness_metrics():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=agentops_harness.get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )

@app.get("/harness/status")
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
    logger.info('Khởi tạo hệ thống AI thành công')
    from src.store.vector_store import vector_store
    from motor.motor_asyncio import AsyncIOMotorClient
    from core.config import settings
    try:
        await vector_store.ensure_collection()
        logger.info('Khởi tạo cơ sở dữ liệu vector thành công')
    except Exception as e:
        logger.error('Lỗi khởi tạo cơ sở dữ liệu vector')
        
    try:
        if settings.MONGODB_URI:
            client = AsyncIOMotorClient(settings.MONGODB_URI)
            db = client.get_default_database()
            await db["finetune_datasets"].create_index([("user_id", 1), ("created_at", -1)], background=True)
            await db["finetune_samples"].create_index([("dataset_id", 1), ("created_at", 1)], background=True)
            await db["finetune_jobs"].create_index([("user_id", 1), ("created_at", -1)], background=True)
            await db["finetune_jobs"].create_index([("dataset_id", 1), ("status", 1)], background=True)
            logger.info('Khởi tạo chỉ mục cơ sở dữ liệu thành công')
    except Exception as e:
        logger.error('Lỗi khởi tạo chỉ mục cơ sở dữ liệu')