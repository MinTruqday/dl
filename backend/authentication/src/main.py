import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.session import router as auth
from src.api.passkey import router as passkey
from src.api.google import router as google
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
from src.core.metrics import PrometheusMiddleware, metrics_collector, metrics_endpoint
app = FastAPI(title="DocLib Authentication", version=settings.VERSION)
app.add_middleware(PrometheusMiddleware, service_name="authentication")
app.add_route("/metrics", metrics_endpoint("authentication"))

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
app.include_router(auth)
app.include_router(passkey)
app.include_router(google)
@app.on_event("startup")
async def startup_event():
    logger.info("Authentication service initialization completed successfully")
    await init_db()
@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
@app.get("/health")
async def health_check():
    return {
        "status": "The authentication service is currently operating normally and functioning as expected without any internal issues"
    }
