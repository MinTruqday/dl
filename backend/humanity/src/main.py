import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
from fastapi import Request
from fastapi.responses import JSONResponse

from src.api.user import router as user_router
from src.api.profile import router as profile_router

app = FastAPI(title="DocLib Humanity", version=settings.VERSION)

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

@app.on_event("startup")
async def startup_event():
    logger.info("Khởi động dịch vụ Humanity")
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Tắt dịch vụ Humanity")
    await close_db()

app.include_router(user_router)
app.include_router(profile_router)
