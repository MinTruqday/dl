from core.middleware import trace_id_ctx_var, trace_id_filter, add_trace_id_header
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uuid
import contextvars
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", filter=trace_id_filter, level="INFO")

from src.api.notification import router as notification_router

app = FastAPI(title="DocLib Signal")
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
    logger.info("Dịch vụ thông báo của DocLib đã sẵn sàng")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "signal"}
