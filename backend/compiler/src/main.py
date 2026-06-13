from core.middleware import trace_id_ctx_var, trace_id_filter, add_trace_id_header
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uuid
import contextvars
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}", filter=trace_id_filter, level="INFO")

from src.api import latex, editor, editorjs

app = FastAPI(title="DocLib Compiler")
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(latex.router, prefix="/bien-dich/latex", tags=["LaTeX"])
app.include_router(editorjs.router, prefix="/bien-dich/editorjs", tags=["EditorJS"])
app.include_router(editor.router, tags=["Editor"])


@app.on_event("startup")
async def startup_event():
    logger.info("Dịch vụ biên dịch DocLib 0.1a đã khởi động")


@app.get("/kiem-tra-suc-khoe")
async def health_check():
    return {"status": "ok", "service": "compiler"}
