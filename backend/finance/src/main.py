import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router import coupon, deposit, monetization, wallet, withdrawal

from core.config import settings
from core.database import close_db, init_db

app = FastAPI(title="DocLib Finance", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include(wallet.router)
app.include(deposit.router)
app.include(withdrawal.router)
app.include(monetization.router)
app.include(coupon.router)


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
