from core.middleware import trace_id_ctx_var, trace_id_filter, add_trace_id_header
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uuid
import contextvars
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}", filter=trace_id_filter, level="INFO")

from src.api.wallet import router as wallet_router
from src.api.deposit import router as deposit_router
from src.api.withdrawal import router as withdrawal_router
from src.api.coupon import router as coupon_router

app = FastAPI(title="DocLib Finance")
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallet_router)
app.include_router(deposit_router)
app.include_router(withdrawal_router)
app.include_router(coupon_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Dịch vụ tài chính đã khởi động")

@app.get("/kiem-tra-suc-khoe")
async def health_check():
    return {"status": "ok", "service": "finance"}
