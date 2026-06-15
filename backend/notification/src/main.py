import sys
from contextlib import asynccontextmanager
from core.config import settings
from core.middleware import add_trace_id_header, trace_id_filter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.notifications import router as notification_router

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    filter=trace_id_filter,
    level="INFO",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Notification service has been successfully initialized and is ready to process incoming requests")
    yield

app = FastAPI(title="DocLib Notification", version=settings.VERSION, lifespan=lifespan)
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notification_router)

@app.get("/health")
async def health_check():
    return {"status": "Notification service is operating normally and functioning as expected without internal issues"}