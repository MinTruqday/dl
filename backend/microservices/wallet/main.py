from fastapi import FastAPI
from shared.core.database import init_db, close_db
from shared.core.config import settings
from .api.wallet import router as wallet_router
from .api.payment import router as payment_router
from .api.payout import router as payout_router
import asyncio
import logging
app = FastAPI(title="DocLib Wallet Service", version="1.0.0")
@app.on_event("startup")
async def startup_event():
    await init_db()
    logging.info("Wallet Service Database initialized")
@app.on_event("shutdown")
async def startup_event():
    await close_db()
    logging.info("Wallet Service Database connection closed")
app.include_router(wallet_router)
app.include_router(payment_router)
app.include_router(payout_router)
@app.get("/health")
async def health():
    return {"status": "wallet_service_running"}
