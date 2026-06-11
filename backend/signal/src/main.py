from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uuid
import contextvars
import sys

trace_id_ctx_var = contextvars.ContextVar("trace_id", default="")


def trace_id_filter(record):
    record["extra"]["trace_id"] = trace_id_ctx_var.get()
    return True


logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[trace_id]}] {message}", filter=trace_id_filter, level="INFO")

from src.router.notification import router as notification_router

app = FastAPI(title="DocLib Signal Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notification_router)


@app.middleware("http")
async def add_trace_id_header(request: Request, call_next):
    trace_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    trace_id_ctx_var.set(trace_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = trace_id
    return response


@app.on_event("startup")
async def startup_event():
    logger.info("DocLib Signal Service initialized")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "signal"}
