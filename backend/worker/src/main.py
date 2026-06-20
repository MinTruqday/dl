import os

import redis.asyncio as redis
from core.config import settings
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Background Task Service", version=settings.VERSION)
redis_client = redis.from_url(settings.REDIS_URI, decode_responses=True)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=503, content={"detail": "Đã xảy ra lỗi, vui lòng thử lại sau"}
    )


@app.get("/health")
async def read_health():
    await redis_client.ping()
    return {"status": "The background processing service is currently operating normally and ready to accept incoming requests"}


@app.post("/documents/compile")
def compile_document(payload: dict):
    doc_id = payload.get("document_id")
    if not doc_id:
        raise HTTPException(status_code=400, detail="Thiếu mã tài liệu hợp lệ để biên dịch")

    from src.tasks import compile_document_tectonic

    task = compile_document_tectonic.delay(doc_id, payload.get("tex_content", ""))
    return {"message": "Đã thêm tài liệu vào hàng đợi", "task_id": task.id}