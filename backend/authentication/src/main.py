import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.auth import router as auth
from src.router.passkey import router as passkey

from core.config import settings
from core.database import close_db, init_db

app = FastAPI(title="DocLib Security", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.CORS_ALLOWED_ORIGINS.split(",")
        if settings.CORS_ALLOWED_ORIGINS
        else ["*"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth)
app.include_router(passkey)


@app.on_event("startup")
async def startup_event():
    logger.info("Tính năng xác thực đã sẵn sàng")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {
        "status": "The authentication service is currently operating normally and functioning as expected without any internal issues"
    }
