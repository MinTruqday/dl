import asyncio
import sys
from contextlib import asynccontextmanager
from core.config import settings
from core.middleware import add_trace_id_header, trace_id_filter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.jobs import router

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
    from src.worker import run_worker
    task = asyncio.create_task(run_worker())
    yield
    task.cancel()
    logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")

app = FastAPI(title="DocLib Collector", version=settings.VERSION, lifespan=lifespan)
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/thu-thap")

@app.get("/suc-khoe")
async def health_check():
    return {
        "status": "Kiểm tra sức khỏe hệ thống hoàn tất và ổn định",
        "service": "crawler_service"
    }