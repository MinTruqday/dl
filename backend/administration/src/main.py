import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.audit_audit_logs import router as audit
from src.api.promotional_banners import router as banner
from src.api.health import router as operation
from src.api.account_profiles import router as profile
from src.api.usage_quotas import router as quota
from src.api.telemetry import router as telemetry
from src.api.profiles import router as user

from shared.infrastructure.config import settings
from shared.infrastructure.database import close_db, init_db

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

app.include_router(user)
app.include_router(audit)
app.include_router(telemetry)
app.include_router(operation)
app.include_router(quota)
app.include_router(profile)
app.include_router(banner)


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
