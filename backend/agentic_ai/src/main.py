import sys
from contextlib import asynccontextmanager
from core.config import settings
from core.middleware import add_trace_id_header, trace_id_filter
from core.repositories.base import RepositoryFactory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.harness.agentops_harness import agentops_harness
from src.harness.evaluation_harness import evaluation_harness
from src.harness.orchestration_harness import orchestration_harness
from src.router.chat import router as chat_router
from src.router.feedback import router as feedback_router
from src.router.finetuning import router as finetune_router
from src.router.history import router as history_router
from src.router.inference import router as inference_router
from src.router.ingestion import router as ingest_router
from src.store.vector_store import vector_store

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("The artificial intelligence system components were initialized and configured successfully")
    try:
        await vector_store.ensure_collection()
        logger.info("The vector database indexing component was successfully initialized and prepared")
    except Exception:
        logger.error("The system failed to initialize the required vector database searching component")
        
    try:
        if settings.MONGODB_URI:
            await RepositoryFactory.get("finetune_datasets").create_index([("user_id", 1), ("created_at", -1)], background=True)
            await RepositoryFactory.get("finetune_samples").create_index([("dataset_id", 1), ("created_at", 1)], background=True)
            await RepositoryFactory.get("finetune_jobs").create_index([("user_id", 1), ("created_at", -1)], background=True)
            await RepositoryFactory.get("finetune_jobs").create_index([("dataset_id", 1), ("status", 1)], background=True)
            logger.info("The primary database collection indexes were created and initialized successfully")
    except Exception:
        logger.error("The system encountered a failure while initializing the essential database indexes")
    yield

app = FastAPI(title="DocLib Agentic AI", version=settings.VERSION, lifespan=lifespan)
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
    return {"status": "System health check passed and service is operating normally"}

@app.get("/evaluate/metrics")
async def harness_metrics():
    return PlainTextResponse(content=agentops_harness.get_prometheus_metrics(), media_type="text/plain; version=0.0.4")

@app.get("/evaluate/status")
async def harness_status():
    return {
        "orchestration": {
            "active_sessions": orchestration_harness.get_active_sessions(),
            "circuit_breaker": orchestration_harness.get_circuit_status(),
        },
        "evaluation": evaluation_harness.get_dashboard_metrics(),
    }