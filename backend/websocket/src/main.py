import uvicorn
from core.config import settings
from core.database import db_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router import editor_ws, message_ws

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

app.include_router(editor_ws.router, prefix="/editor")
app.include_router(message_ws.router, prefix="/messages")


@app.on_event("startup")
async def startup_event():
    logger.info("The real-time communication service has been initialized successfully and is ready to accept incoming connections")
    from core.database import init_db

    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    from core.database import close_db

    await close_db()


@app.get("/health")
async def health_check():
    return {"status": "The real-time communication service is operating normally and functioning as expected"}