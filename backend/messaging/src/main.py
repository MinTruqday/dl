import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.thread import router as message
from src.api.conversation import router as conversation
from src.api.group import router as group
from src.api.interaction import router as interaction
from src.api.pin import router as pin
from src.api.attachment import router as attachment
from src.api.enhancement import router as enhancement
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
from src.core.metrics import PrometheusMiddleware, metrics_collector, metrics_endpoint
app = FastAPI(title="DocLib Massaging", version=settings.VERSION)
app.add_middleware(PrometheusMiddleware, service_name="messaging")
app.add_route("/metrics", metrics_endpoint("messaging"))

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
app.include_router(conversation)
app.include_router(message)
app.include_router(group)
app.include_router(interaction)
app.include_router(pin)
app.include_router(attachment)
app.include_router(enhancement)
@app.on_event("startup")
async def startup_event():
    logger.info("Message service initialization completed successfully")
    await init_db()
@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
@app.get("/health")
async def health_check():
    return {
        "status": "The communication service is currently operating normally and functioning as expected without any internal issues"
    }
