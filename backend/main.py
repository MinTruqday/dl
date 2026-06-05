from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from brotli_asgi import BrotliMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from core.database import init_db, close_db, db_client
from core.config import settings
from core.storage import initialize_bucket
from core.worker import start_workers
from services.cron import start_cron_service
from prometheus_fastapi_instrumentator import Instrumentator
from loguru import logger
import asyncio
import os
import sys
import time

from api.authentication import router as auth_router
from api.document import router as document_router
from api.upload import router as upload_router
from api.profile import router as profile_router
from api.editor import router as editor_router
from api.version import router as version_router
from api.review import router as review_router
from api.highlight import router as highlight_router
from api.notification import router as notification_router
from api.wallet import router as wallet_router
from api.export import router as export_router
from api.deposit import router as deposit_router
from api.reading import router as reading_router
from api.monetization import router as monetization_router
from api.withdrawal import router as withdrawal_router
from api.rag import router as rag_router
from api.inference import router as inference_router
from api.message import router as message_router
from api.latex import router as latex_router
from api.collector import router as collector_router
from api.library import router as library_router
from api.feedback import router as feedback_router
from api.ai import router as ai_router
from api.operation import router as operation_router
from api.draft import router as draft_router
from api.report import router as report_router
from api.audit import router as audit_router
from api.telemetry import router as telemetry_router
from api.banner import router as banner_router
from api.user import router as user_router
from api.discovery import router as discovery_router
from api.passkey import router as passkey_router
from api.publication import router as publish_router
from api.coupon import router as coupon_router
from api.collaboration import router as collaboration_router
from api.compilation import router as compilation_router
from api.bookmark import router as bookmark_router
from api.pin import router as pin_router
from api.preference import router as preference_router
from api.quota import router as quota_router
from api.storage import router as storage_router
from api.finetune import router as finetune_router

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

app.add_middleware(
    BrotliMiddleware,
    quality=5,
    minimum_size=500
)

from fastapi.responses import Response, FileResponse
from core.storage import get_storage_client


from fastapi import Query

@app.get("/document/{file_path:path}")
async def serve_document(file_path: str, token: str = Query(None)):
    local_path = os.path.join("assets/document", file_path)
    if os.path.exists(local_path) and os.path.isfile(local_path):
        return FileResponse(local_path)
        
    if file_path.endswith(('.pdf', '.zip', '.docx')):
        user = None
        if token:
            from api.dependency import get_current_user_token_param
            try:
                user = await get_current_user_token_param(token)
            except Exception:
                pass
                
        from core.database import db_client
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"file_url": {"$in": [file_path, f"/{file_path}", f"documents/{file_path}"]}})
        if doc and doc.get("is_premium"):
            if not user:
                raise HTTPException(status_code=401, detail="Cần đăng nhập để tải tài liệu này")
            if str(doc.get("author_id")) != str(user.id) and user.role not in ["ADMIN", "MODERATOR"]:
                purchase = await db["purchases"].find_one({"user_id": str(user.id), "item_id": str(doc["_id"])})
                if not purchase:
                    raise HTTPException(status_code=403, detail="Bạn chưa mua tài liệu này")
    try:
        from core.storage import get_s3_client
        async with await get_s3_client() as s3:
            object_key = f"documents/{file_path}"
            response = await s3.get_object(Bucket=settings.MINIO_BUCKET_NAME, Key=object_key)
            content = await response["Body"].read()
            return Response(content, media_type=response.get("ContentType", "application/pdf"))
    except Exception as e:
        logger.error(f"Error serving document '{file_path}' from MinIO: {e}")
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/storage/{file_path:path}")
async def serve_storage(file_path: str):
    local_path = os.path.join("assets", file_path)
    if os.path.exists(local_path) and os.path.isfile(local_path):
        return FileResponse(local_path)
    try:
        from core.storage import get_storage_client
        async with await get_storage_client() as storage_client:
            response = await storage_client.get_object(Bucket=settings.MINIO_BUCKET_NAME, Key=file_path)
            content = await response["Body"].read()
            return Response(content, media_type=response.get("ContentType", "application/octet-stream"))
    except Exception as e:
        logger.error(f"Error serving storage '{file_path}' from MinIO: {e}")
        raise HTTPException(status_code=404, detail="File not found")

os.makedirs("assets/document", exist_ok=True)
app.mount("/document", StaticFiles(directory="assets/document"), name="document")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "message": str(exc.detail), "status": exc.status_code}
    )
    origin = request.headers.get("origin")
    if origin in allowed_origins or "*" in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = "Dữ liệu không hợp lệ: " + ", ".join([f"{e['loc'][-1]}: {e['msg']}" for e in errors])
    response = JSONResponse(
        status_code=422,
        content={"data": {"errors": errors}, "message": msg, "status": 422}
    )
    origin = request.headers.get("origin")
    if origin in allowed_origins or "*" in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception on {request.method} {request.url}: {repr(exc)}")
    response = JSONResponse(
        status_code=500,
        content={
            "data": None, 
            "message": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau", 
            "status": 500
        }
    )
    origin = request.headers.get("origin")
    if origin in allowed_origins or "*" in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
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
    start_cron_service()
    instrumentator.expose(app)

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(wallet_router)
app.include_router(deposit_router)
app.include_router(export_router)
app.include_router(upload_router)
app.include_router(document_router)
app.include_router(review_router)
app.include_router(version_router)
app.include_router(latex_router)
app.include_router(editor_router)
app.include_router(monetization_router)
app.include_router(reading_router)
app.include_router(highlight_router)
app.include_router(library_router)
app.include_router(feedback_router)
app.include_router(ai_router)
app.include_router(rag_router)
app.include_router(inference_router)
app.include_router(notification_router)
app.include_router(message_router)
app.include_router(collector_router)
app.include_router(withdrawal_router)
app.include_router(operation_router)
app.include_router(draft_router)
app.include_router(report_router)
app.include_router(audit_router)
app.include_router(telemetry_router)
app.include_router(banner_router)
app.include_router(user_router)
app.include_router(discovery_router)
app.include_router(passkey_router)
app.include_router(publish_router)
app.include_router(coupon_router)
app.include_router(collaboration_router)
app.include_router(compilation_router)
app.include_router(bookmark_router)
app.include_router(pin_router)
app.include_router(preference_router)
app.include_router(quota_router)
app.include_router(storage_router)
app.include_router(finetune_router)

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
