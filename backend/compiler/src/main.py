import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api import latex, editorjs

app = FastAPI(title="DocLib Compiler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(latex.router, prefix="/bien-dich/latex")
app.include_router(editorjs.router, prefix="/bien-dich/editorjs")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting DocLib Compiler")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "DocLib Compiler"}
