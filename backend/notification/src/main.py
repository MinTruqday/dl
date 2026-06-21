import contextvars
import sys
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from core.middleware import add_trace_id_header, trace_id_ctx_var, trace_id_filter

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    filter=trace_id_filter,
    level="INFO",
)

from src.api.push_notification import router as notification

from core.config import settings

app = FastAPI(title="DocLib Signal", version=settings.VERSION)
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notification)


@app.on_event("startup")
async def startup_event():
    logger.info("Khởi tạo thông báo thành công")


@app.get("/health")
async def health_check():
    return {
        "status": "The signaling service is currently operating normally and functioning as expected without any internal issues"
    }
