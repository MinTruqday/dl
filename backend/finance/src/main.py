import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.deposit import router as deposit
from src.api.monetization import router as monetization
from src.api.wallet import router as wallet
from src.api.withdrawal import router as withdrawal
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
app = FastAPI(title="DocLib Payment", version=settings.VERSION)
app.add_middleware(PrometheusMiddleware, service_name="finance")
app.add_route("/metrics", metrics_endpoint("finance"))

from fastapi import Request
from fastapi.responses import JSONResponse
from src.core.metrics import PrometheusMiddleware, metrics_collector, metrics_endpoint
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
app.include_router(wallet)
app.include_router(deposit)
app.include_router(withdrawal)
app.include_router(monetization)
@app.on_event("startup")
async def startup_event():
    import asyncio
    from src.outbox_worker import process_outbox
    from src.core.infrastructure.database import init_db
    logger.info("Financial management service provisioned and ready")
    await init_db()
    asyncio.create_task(process_outbox())
@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
@app.get("/health")
async def health_check():
    return {
        "status": "The financial management service is currently operating normally and functioning as expected without any internal issues"
    }
