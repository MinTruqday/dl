import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.coupon import router as coupon
from src.api.deposit import router as deposit
from src.api.monetization import router as monetization
from src.api.wallet import router as wallet
from src.api.withdrawal import router as withdrawal

from shared.infrastructure.configuration import settings
from shared.infrastructure.database import close_db, init_db

app = FastAPI(title="DocLib Finance", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallet)
app.include_router(deposit)
app.include_router(withdrawal)
app.include_router(monetization)
app.include_router(coupon)


@app.on_event("startup")
async def startup_event():
    logger.info("Tính năng thanh toán đã sẵn sàng")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {
        "status": "The financial management service is currently operating normally and functioning as expected without any internal issues"
    }
