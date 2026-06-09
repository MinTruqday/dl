from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

from src.api.wallet import router as wallet_router
from src.api.deposit import router as deposit_router
from src.api.withdrawal import router as withdrawal_router
from src.api.coupon import router as coupon_router
from src.api.monetization import router as monetization_router

app = FastAPI(title="DocLib Finance")

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
    logger.info("Starting DocLib Finance")
    from src.core.database import connect_to_mongo
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    from src.core.database import close_mongo_connection
    await close_mongo_connection()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "DocLib Finance"}
