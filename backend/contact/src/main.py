import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.message_router import router as message_router

app = FastAPI(title="DocLib Contact", version=settings.VERSION)

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

app.include_router(message_router)


@app.on_event("startup")
async def startup_event():
    logger.info("The internal contact and messaging service has been successfully initialized and is now ready to process incoming requests")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {"status": "The communication service is currently operating normally and functioning as expected without any internal issues"}