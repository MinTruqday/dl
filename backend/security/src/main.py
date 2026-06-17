import uvicorn
from core.config import settings
from loguru import logger
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.router.auth_router import router as auth_router
from src.router.passkey_router import router as passkey_router

app = FastAPI(title="DocLib Security", version=settings.VERSION)

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

app.include_router(auth_router)
app.include_router(passkey_router)


@app.on_event("startup")
async def startup_event():
    logger.info("The security and authentication service has been initialized successfully and is ready to accept incoming connections")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {"status": "The authentication service is currently operating normally and functioning as expected without any internal issues"}