from fastapi import FastAPI
from shared.core.database import init_db, close_db
from shared.core.config import settings
from .api.authentication import router as auth_router
from .api.passkey import router as passkey_router
import asyncio
import logging
app = FastAPI(title="DocLib Auth Service", version="1.0.0")
@app.on_event("startup")
async def startup_event():
    await init_db()
    logging.info("Auth Service Database initialized")
@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
    logging.info("Auth Service Database connection closed")
app.include_router(auth_router)
app.include_router(passkey_router)
@app.get("/health")
async def health():
    return {"status": "auth_service_running"}
