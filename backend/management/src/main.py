import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.audit import router as audit
from src.router.banner import router as banner
from src.router.operation import router as operation
from src.router.profile import router as profile
from src.router.quota import router as quota
from src.router.telemetry import router as telemetry
from src.router.user import router as user

from core.config import settings
from core.database import close_db, init_db

app = FastAPI(title="DocLib Provision", version=settings.VERSION)

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

app.include(user)
app.include(audit)
app.include(telemetry)
app.include(operation)
app.include(quota)
app.include(profile)
app.include(banner)


@app.on_event("startup")
async def startup_event():
    logger.info("Tính năng cung cấp đã sẵn sàng")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {
        "status": "The provision service is currently operating normally and functioning as expected without any internal issues"
    }
