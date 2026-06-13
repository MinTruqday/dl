from loguru import logger
import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.router.audit_router import router as audit_router
from src.router.operation_router import router as operation_router
from src.router.quota_router import router as quota_router
from src.router.telemetry_router import router as telemetry_router
from src.router.user_router import router as user_router

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

app.include_router(user_router)
app.include_router(audit_router)
app.include_router(telemetry_router)
app.include_router(operation_router)
app.include_router(quota_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Đã khởi tạo hệ thống quản lý DocLib")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "provision"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8050, reload=True)
