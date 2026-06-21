import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.document_sync import router as editor_socket
from src.api.live_chat import router as message_socket

from core.infrastructure.app_config import settings
from core.infrastructure.database_client import db_client

app = FastAPI(title="WebSocket Service", version=settings.VERSION)

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

app.include_router(editor_socket)
app.include_router(message_socket)


@app.on_event("startup")
async def startup_event():
    logger.info("Tính năng tin nhắn đã sẵn sàng")
    from core.infrastructure.database_client import init_db

    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    from core.infrastructure.database_client import close_db

    await close_db()


@app.get("/health")
async def health_check():
    return {
        "status": "The real-time communication service is operating normally and functioning as expected"
    }
