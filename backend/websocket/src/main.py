import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.composition import router as composition_socket
from src.api.message import router as message_socket
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
app = FastAPI(title="DocLib WebSocket", version=settings.VERSION)

from fastapi import Request
from fastapi.responses import JSONResponse
@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if "/internal/" in request.url.path:
        token = request.headers.get("X-Internal-Token")
        if token != settings.SECRET_KEY:
            return JSONResponse(status_code=403, content={"detail": "Forbidden invalid internal token"})
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
app.include_router(composition_socket)
app.include_router(message_socket)
@app.on_event("startup")
async def startup_event():
    logger.info("WebSocket service initialized successfully")
@app.on_event("shutdown")
async def shutdown_event():
    from src.core.infrastructure.database import close_db
    await close_db()
@app.get("/health")
async def health_check():
    return {
        "status": "The real-time communication service is operating normally and functioning as expected"
    }
