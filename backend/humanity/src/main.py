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
from src.core.metrics import PrometheusMiddleware, metrics_collector, metrics_endpoint

app = FastAPI(title="DocLib Humanity", version=settings.VERSION)
app.add_middleware(PrometheusMiddleware, service_name="humanity")
app.add_route("/metrics", metrics_endpoint("humanity"))

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

@app.on_event("startup")
async def startup_event():
    logger.info("Humanity microservice starting up")
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Humanity microservice shutting down gracefully")
    await close_db()

app.include_router(user_router)
app.include_router(profile_router)
