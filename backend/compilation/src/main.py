import contextvars
import sys
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.core.middleware import add_trace_id_header, trace_id_ctx_var, trace_id_filter
from src.core.metrics import PrometheusMiddleware, metrics_collector, metrics_endpoint
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}",
    filter=trace_id_filter,
    level="INFO",
)
from src.api.composition import router as editor
from src.api.composition import router as editorjs
from src.api.latex import router as latex
from src.api.cortex import router as cortex
from src.core.infrastructure.configuration import settings
app = FastAPI(title="DocLib Compiler", version=settings.VERSION)
app.add_middleware(PrometheusMiddleware, service_name="compilation")
app.add_route("/metrics", metrics_endpoint("compilation"))

from fastapi import Request
from fastapi.responses import JSONResponse
@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if "/internal/" in request.url.path:
        token = request.headers.get("X-Internal-Token")
        if token != settings.SECRET_KEY:
            return JSONResponse(status_code=403, content={"detail": "Forbidden invalid internal token"})
    return await call_next(request)

app.middleware("http")(add_trace_id_header)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(latex)
app.include_router(cortex)
app.include_router(editorjs)
app.include_router(editor)
@app.on_event("startup")
async def startup_event():
    logger.info("Document compilation service successfully initialized and running")
@app.get("/health")
async def health_check():
    return {
        "status": "The document compilation service is currently operating normally and functioning as expected without any internal issues",
        "service": "document_compiler",
    }
@app.on_event("shutdown")
async def shutdown_event():
    try:
        from src.core.infrastructure.redis import redis
        await redis.aclose()
    except Exception:
        pass
    try:
        from src.core.infrastructure.mq import mq
        await mq.aclose()
    except Exception:
        pass
