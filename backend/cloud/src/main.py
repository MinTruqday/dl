import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db
from src.api.storage import router as storage
from src.api.upload import router as upload
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
)
app = FastAPI(title="DocLib Cloud", version=settings.VERSION)

from fastapi import Request
from fastapi.responses import JSONResponse
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
app.include_router(storage)
app.include_router(upload)
@app.on_event("startup")
async def startup_event():
    logger.info("Cloud storage service provisioned and ready")
    await init_db()
    from src.core.storage import initialize_bucket
    await initialize_bucket()

from fastapi.responses import RedirectResponse
from src.services.upload import UploadService

@app.get("/storage/{file_path:path}")
async def get_storage_file(file_path: str):
    url_data = await UploadService.get_presigned_url(file_path)
    return RedirectResponse(url=url_data["download_url"], status_code=302)
@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
@app.get("/health")
async def health_check():
    return {
        "status": "Cloud service is healthy"
    }
