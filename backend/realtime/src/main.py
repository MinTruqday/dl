import uvicorn
from contextlib import asynccontextmanager
from core.config import settings
from core.database import close_db, db_client, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router import editor, messages

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Real-time communication service initialized successfully and ready to accept incoming connections")
    await init_db()
    yield
    await close_db()
    logger.info("Real-time communication service has been shut down cleanly and all connections closed")

app = FastAPI(title="Real-time Service", version=settings.VERSION, lifespan=lifespan)

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

app.include_router(editor.router, prefix="/editor")
app.include_router(messages.router, prefix="/messages")

@app.get("/health")
async def check_health():
    return {"status": "Real-time communication service is operating normally and functioning as expected"}