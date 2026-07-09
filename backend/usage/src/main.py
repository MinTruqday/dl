import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
from fastapi import Request
from fastapi.responses import JSONResponse

from src.api.tier import router as tier_router
from src.api.quota import router as quota_router
from src.core.metrics import PrometheusMiddleware, metrics_collector, metrics_endpoint

app = FastAPI(title="DocLib Usage", version=settings.VERSION)
app.add_middleware(PrometheusMiddleware, service_name="usage")
app.add_route("/metrics", metrics_endpoint("usage"))

@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if "/internal/" in request.url.path:
        token = request.headers.get("X-Internal-Token")
        if token != settings.SECRET_KEY:
            return JSONResponse(status_code=403, content={"detail": "Từ chối truy cập: Mã thông báo xác thực nội bộ không hợp lệ"})
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Usage management service provisioned and ready")
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Usage management service shutting down")
    await close_db()

app.include_router(tier_router)
app.include_router(quota_router)
