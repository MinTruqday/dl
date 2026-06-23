import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.chat_threads import router as message

from shared.infrastructure.config import settings
from shared.infrastructure.database import close_db, init_db

app = FastAPI(title="DocLib Massaging", version=settings.VERSION)

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

app.include_router(message)


@app.on_event("startup")
async def startup_event():
    logger.info("Khởi tạo tin nhắn thành công")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {
        "status": "The communication service is currently operating normally and functioning as expected without any internal issues"
    }
