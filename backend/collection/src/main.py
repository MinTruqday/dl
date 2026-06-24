import asyncio
import contextvars
import sys
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from shared.middleware import add_trace_id_header, trace_id_ctx_var, trace_id_filter

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)

from src.api.ingestion import router as collector

from shared.infrastructure.configuration import settings

app = FastAPI(title="DocLib Crawler", version=settings.VERSION)
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(collector)


@app.on_event("startup")
async def startup_event():
    logger.info("Tính năng thu thập dữ liệu đã sẵn sàng")
    from src.services.queue import run_worker

    asyncio.create_task(run_worker())


@app.get("/health")
async def health_check():
    return {
        "status": "The automated data collection service is currently operating normally and functioning as expected",
        "service": "crawler",
    }
