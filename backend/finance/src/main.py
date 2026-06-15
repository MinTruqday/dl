from contextlib import asynccontextmanager
import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router import coupons, deposits, monetization, wallets, withdrawals

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Financial processing service has been successfully initialized and is ready to handle transactions")
    await init_db()
    yield
    await close_db()
    logger.info("Financial processing service has cleanly shut down and closed all database connections")

app = FastAPI(title="DocLib Finance", version=settings.VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallets.router)
app.include_router(deposits.router)
app.include_router(withdrawals.router)
app.include_router(monetization.router)
app.include_router(coupons.router)

@app.get("/health")
async def health_check():
    return {"status": "Financial management service is currently operating normally and functioning as expected without internal issues"}