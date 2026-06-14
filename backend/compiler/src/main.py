import contextvars
import sys
import uuid

from core.middleware import add_trace_id_header, trace_id_ctx_var, trace_id_filter
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)

from src.router import (
    editor_router as editor,
    editorjs_router as editorjs,
    latex_router as latex,
)
from core.config import settings

app = FastAPI(title="DocLib Compiler", version=settings.VERSION)
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(latex.router)
app.include_router(editorjs.router)
app.include_router(editor.router)


@app.on_event("startup")
async def startup_event():
    logger.info("The document compilation service has been successfully initialized and is now ready to accept incoming requests")


@app.get("/health")
async def health_check():
    return {"status": "The document compilation service is currently operating normally and functioning as expected without any internal issues", "service": "document_compiler"}