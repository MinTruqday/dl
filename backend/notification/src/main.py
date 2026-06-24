import contextvars
import sys
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.core.middleware import add_trace_id_header, trace_id_ctx_var, trace_id_filter

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    filter=trace_id_filter,
    level="INFO",
)

from src.api.announcement import router as notification

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db

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
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {
        "status": "The signaling service is currently operating normally and functioning as expected without any internal issues"
    }
