import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.router import router

app = FastAPI(title="DocLib Collector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/thu-thap")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Collector API & Worker")
    from src.worker import run_worker
    asyncio.create_task(run_worker())

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "DocLib Collector"}

