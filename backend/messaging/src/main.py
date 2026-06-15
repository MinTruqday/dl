from contextlib import asynccontextmanager
import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.messages import router as message_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Internal messaging service has been successfully initialized and is ready to process incoming requests")
    await init_db()
    yield
    await close_db()
    logger.info("Internal messaging service has safely shut down and closed all active database connections")

app = FastAPI(title="DocLib Messaging", version=settings.VERSION, lifespan=lifespan)

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

app.include_router(message_router)

@app.get("/health")
async def health_check():
    return {"status": "Messaging communication service is operating normally and functioning as expected without internal issues"}