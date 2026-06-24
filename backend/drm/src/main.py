import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from shared.middleware import add_trace_id_header, trace_id_filter
from shared.infrastructure.configuration import settings
from shared.infrastructure.database import close_db, init_db

from src.api.license import router as license_router
from src.api.watermark import router as watermark_router

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    filter=trace_id_filter,
    level="INFO",
)

app = FastAPI(title="DocLib DRM", version=settings.VERSION)
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(license_router)
app.include_router(watermark_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Khởi tạo DRM thành công")
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/health")
async def health_check():
    return {
        "status": "DRM service is healthy"
    }
