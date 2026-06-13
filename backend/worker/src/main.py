import os

import redis.asyncio as redis
from core.config import settings
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Hệ thống tác vụ biên dịch AI", version="2.0.26")
redis_client = redis.from_url(settings.REDIS_URI, decode_responses=True)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=503, content={"detail": "Lỗi dịch vụ vui lòng thử lại sau"}
    )


@app.get("/health")
async def read_health():
    await redis_client.ping()
    return {"status": "healthy"}


@app.post("/cong-viec/tectonic/bien-dich")
def compile_document(payload: dict):
    doc_id = payload.get("document_id")
    if not doc_id:
        raise HTTPException(status_code=400, detail="Thiếu mã tài liệu")

    from src.tasks import compile_document_tectonic

    task = compile_document_tectonic.delay(doc_id, payload.get("tex_content", ""))
    return {"message": "Đã đưa tài liệu vào hàng đợi xử lý", "task_id": task.id}
