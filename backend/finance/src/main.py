import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router import (
    coupon_router,
    deposit_router,
    monetization_router,
    wallet_router,
    withdrawal_router,
)

app = FastAPI(title="DocLib Finance", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallet_router.router)
app.include_router(deposit_router.router)
app.include_router(withdrawal_router.router)
app.include_router(monetization_router.router)
app.include_router(coupon_router.router)


@app.on_event("startup")
async def startup_event():
    logger.info("The financial processing service has been successfully initialized and is now ready to handle transactions")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {"status": "The financial management service is currently operating normally and functioning as expected without any internal issues"}