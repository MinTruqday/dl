import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

from src.api.authentication import router as auth_router
from src.api.identity import router as identity_router

app = FastAPI(title="DocLib Authentication")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(identity_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting DocLib Authentication")
    from src.core.database import connect_to_db
    await connect_to_db()

@app.on_event("shutdown")
async def shutdown_event():
    from src.core.database import close_db
    await close_db()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "DocLib Authentication"}
