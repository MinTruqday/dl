import contextvars
import sys
import uuid

from core.middleware import add_trace_id_header, trace_id_ctx_var, trace_id_filter
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    filter=trace_id_filter,
    level="INFO",
)

from core.config import settings
from src.router.notification_router import router as notification_router

app = FastAPI(title="DocLib Signal", version=settings.VERSION)
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notification_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Đã khởi tạo hệ thống thông báo DocLib")


@app.get("/trang-thai")
async def health_check():
    return {"status": "healthy", "service": "signal"}
