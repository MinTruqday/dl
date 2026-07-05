import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.audit import router as audit
from src.api.health import router as operation
from src.api.telemetry import router as telemetry
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
app = FastAPI(title="DocLib Management", version=settings.VERSION)

from fastapi import Request
from fastapi.responses import JSONResponse
@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if "/internal/" in request.url.path:
        token = request.headers.get("X-Internal-Token")
        if token != settings.SECRET_KEY:
            return JSONResponse(status_code=403, content={"detail": "Forbidden: Invalid internal token"})
    return await call_next(request)

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
app.include_router(audit)
app.include_router(telemetry)
app.include_router(operation)
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
