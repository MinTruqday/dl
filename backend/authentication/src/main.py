from contextlib import asynccontextmanager
import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.auth import router as auth_router
from src.router.passkey import router as passkey_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Security and authentication service initialized successfully and ready to accept incoming connections")
    await init_db()
    yield
    await close_db()

app = FastAPI(title="DocLib Authentication", version=settings.VERSION, lifespan=lifespan)

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

app.include_router(auth_router)
app.include_router(passkey_router)

@app.get("/health")
async def health_check():
    return {"status": "Authentication service is operating normally and functioning as expected without internal issues"}