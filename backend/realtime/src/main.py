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
    logger.info("Quá trình khởi tạo dịch vụ và kết nối cơ sở dữ liệu thành công")
    await init_db()
    yield
    await close_db()
    logger.info("Dịch vụ đã ngắt kết nối cơ sở dữ liệu và dừng an toàn")

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

app.include_router(editor.router, prefix="/soan-thao")
app.include_router(messages.router, prefix="/tin-nhan")

@app.get("/suc-khoe")
async def check_health():
    return {"status": "Kiểm tra sức khỏe hệ thống hoàn tất và ổn định"}