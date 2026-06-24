from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.rabbitmq_client import rabbitmq
from src.api.queue_api import router as queue_router

app = FastAPI(title="DocLib Queue Proxy", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(queue_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Service Queue Proxy đã sẵn sàng")
    await rabbitmq.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await rabbitmq.close()

@app.get("/health")
async def health_check():
    return {
        "status": "The queue proxy service is operating normally",
        "service": "queue"
    }
