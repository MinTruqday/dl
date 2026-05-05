from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from core.database import init_db, close_db, db_client
from core.config import settings
from core.storage import initialize_bucket
from core.worker import start_workers
from prometheus_fastapi_instrumentator import Instrumentator
from loguru import logger
import asyncio
import os
import sys
import time

from api.auth import router as auth_router
from api.asset import router as asset_router
from api.comment import router as comment_router
from api.document import router as document_router
from api.upload import router as upload_router
from api.profile import router as profile_router
from api.social import router as social_router
from api.editor import router as editor_router
from api.coauthor import router as coauthor_router
from api.version import router as version_router
from api.review import router as review_router
from api.highlight import router as highlight_router
from api.notification import router as notification_router
from api.wallet import router as wallet_router
from api.payment import router as payment_router
from api.export import router as export_router
from api.gateway import router as gateway_router
from api.read import router as read_router
from api.monetization import router as monetization_router
from api.payout import router as payout_router
from api.story import router as story_router
from api.rag import router as rag_router
from api.inference import router as inference_router
from api.chat import router as chat_router
from api.latex import router as latex_router
from api.collector import router as collector_router
from api.library import router as library_router
from api.feedback import router as feedback_router
from api.ai import router as ai_router
from api.operation import router as operation_router
from api.draft import router as draft_router
from api.report import router as report_router
from api.log import router as log_router
from api.telemetry import router as telemetry_router
from api.banner import router as banner_router
from api.user import router as user_router
from api.discovery import router as discovery_router
from api.passkey import router as passkey_router
from api.publish import router as publish_router
from api.coupon import router as coupon_router

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
logger.add("logs/backend.log", rotation="10 MB", level="INFO")

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, docs_url="/docs", redoc_url="/redoc")

allowed_origins = [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("public/feed_uploads", exist_ok=True)
os.makedirs("public/uploads", exist_ok=True)
app.mount("/feed_uploads", StaticFiles(directory="public/feed_uploads"), name="feed_uploads")
app.mount("/uploads", StaticFiles(directory="public/uploads"), name="uploads")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    response = JSONResponse(status_code=422, content={"detail": exc.errors()})
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception on {request.method} {request.url}: {repr(exc)}")
    response = JSONResponse(
        status_code=500,
        content={"detail": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau."},
    )
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

instrumentator = Instrumentator().instrument(app)

@app.on_event("startup")
async def startup_event():
    await init_db()
    asyncio.create_task(initialize_bucket())
    asyncio.create_task(start_workers())
    instrumentator.expose(app)

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

app.include_router(auth_router, prefix="")
app.include_router(asset_router)
app.include_router(profile_router, prefix="")
app.include_router(wallet_router, prefix="/wallet")
app.include_router(payment_router, prefix="/payment")
app.include_router(gateway_router, prefix="/gateways")
app.include_router(export_router)
app.include_router(upload_router)
app.include_router(social_router, prefix="")
app.include_router(story_router, prefix="")
app.include_router(comment_router, prefix="")
app.include_router(document_router, prefix="")
app.include_router(review_router, prefix="")
app.include_router(version_router, prefix="")
app.include_router(latex_router)
app.include_router(editor_router)
app.include_router(monetization_router)
app.include_router(read_router)
app.include_router(library_router)
app.include_router(feedback_router)
app.include_router(ai_router)
app.include_router(rag_router)
app.include_router(inference_router)
app.include_router(notification_router)
app.include_router(chat_router)
app.include_router(coauthor_router)
app.include_router(collector_router)
app.include_router(payout_router, tags=["payout"])
app.include_router(operation_router, prefix="/operation", tags=["operation"])
app.include_router(draft_router, tags=["draft"])
app.include_router(report_router, tags=["reports"])
app.include_router(log_router, tags=["logs"])
app.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])
app.include_router(banner_router, tags=["banner"])
app.include_router(user_router)
app.include_router(discovery_router)
app.include_router(passkey_router)
app.include_router(publish_router)
app.include_router(coupon_router)

@app.get("/health")
async def health_check():
    db_status = "ok"
    redis_status = "ok"
    try:
        await db_client.mongodb.admin.command('ping')
    except:
        db_status = "error"
    
    if db_client.redis:
        try:
            await db_client.redis.ping()
        except:
            redis_status = "error"
    else:
        redis_status = "not_configured"
        
    try:
        cpu_load = os.getloadavg()[0] / os.cpu_count() * 100
    except Exception:
        cpu_load = 0.0
        
    try:
        statvfs = os.statvfs('/')
        disk_usage = (statvfs.f_blocks - statvfs.f_bfree) / statvfs.f_blocks * 100
    except Exception:
        disk_usage = 0.0

    return {
        "status": "ok" if db_status == "ok" and (redis_status == "ok" or redis_status == "not_configured") else "degraded",
        "services": {
            "api": "ok",
            "mongodb": db_status,
            "redis": redis_status
        },
        "resources": {
            "cpu_usage": f"{min(cpu_load, 100):.1f}%",
            "memory_usage": "N/A", 
            "disk_usage": f"{disk_usage:.1f}%"
        },
        "version": "1.0.0-production"
    }
