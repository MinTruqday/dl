import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

from src.api.audit import router as audit_router
from src.api.telemetry import router as telemetry_router
from src.api.operation import router as operation_router
from src.api.user import router as user_router

app = FastAPI(title="DocLib Provision")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router)
app.include_router(telemetry_router)
app.include_router(operation_router)
app.include_router(user_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting DocLib Provision")
    from src.core.database import connect_to_mongo
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    from src.core.database import close_mongo_connection
    await close_mongo_connection()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "DocLib Provision"}
