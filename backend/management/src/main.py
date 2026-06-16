from contextlib import asynccontextmanager
import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.audit import router as audit_router
from src.router.operations import router as operation_router
from src.router.quotas import router as quota_router
from src.router.telemetry import router as telemetry_router
from src.router.users import router as user_router
from src.router.profiles import router as profile_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Quá trình khởi tạo dịch vụ và kết nối cơ sở dữ liệu thành công")
    await init_db()
    yield
    await close_db()

app = FastAPI(title="DocLib Management", version=settings.VERSION, lifespan=lifespan)

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
app.include_router(profile_router)

@app.get("/suc-khoe")
async def health_check():
    return {"status": "Kiểm tra sức khỏe hệ thống hoàn tất và ổn định"}