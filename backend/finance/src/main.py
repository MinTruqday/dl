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
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)

from src.router.coupon_router import router as coupon_router
from src.router.deposit_router import router as deposit_router
from src.router.wallet_router import router as wallet_router
from src.router.withdrawal_router import router as withdrawal_router
from src.router.monetization_router import router as monetization_router
from core.config import settings

app = FastAPI(title="DocLib Finance", version=settings.VERSION)
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
app.include_router(monetization_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Finance subsystem initialized successfully")


@app.get("/trang-thai")
async def health_check():
    return {"status": "ok", "service": "finance"}
