import sys
from contextlib import asynccontextmanager
from core.config import settings
from core.middleware import add_trace_id_header, trace_id_filter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.editor import router as editor_router
from src.router.editorjs import router as editorjs_router
from src.router.latex import router as latex_router

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Document compilation and editor service successfully initialized and ready to accept incoming requests")
    yield

app = FastAPI(title="DocLib Editor", version=settings.VERSION, lifespan=lifespan)
app.middleware("http")(add_trace_id_header)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(latex_router)
app.include_router(editorjs_router)
app.include_router(editor_router)

@app.get("/health")
async def health_check():
    return {
        "status": "Document editor service is currently operating normally and functioning as expected without internal issues",
        "service": "document_editor"
    }