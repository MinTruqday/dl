import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.core.middleware import add_trace_id_header, trace_id_filter
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
from src.api.license import router as license_router
from src.api.watermark import router as watermark_router
from src.api.copyright import router as copyright_router
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    filter=trace_id_filter,
    level="INFO",
)
app = FastAPI(title="DocLib DRM", version=settings.VERSION)

from fastapi import Request
from fastapi.responses import JSONResponse
@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if "/internal/" in request.url.path:
        token = request.headers.get("X-Internal-Token")
        if token != settings.SECRET_KEY:
            return JSONResponse(status_code=403, content={"detail": "Forbidden invalid internal token"})
    return await call_next(request)

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
app.include_router(copyright_router)
@app.on_event("startup")
async def startup_event():
    logger.info("DRM service initialized successfully")
    await init_db()
@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
@app.get("/health")
async def health_check():
    return {
        "status": "DRM service is healthy"
    }
