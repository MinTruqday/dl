import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from pydantic import BaseModel

from core.config import settings

app = FastAPI(title="Hệ thống tác vụ biên dịch AI", version="2.0.26")
redis_client = redis.from_url(settings.REDIS_URI, decode_responses=True)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=503,
        content={"detail": "Bạn không thể thực hiện thao tác này ngay lúc này. Vui lòng thử lại sau."}
    )

@app.get("/health")
async def read_health():
    await redis_client.ping()
    return {"status": "Hệ thống hoạt động bình thường."}

@app.post("/tasks/tectonic/compile")
def compile_document(payload: dict):
    doc_id = payload.get("document_id")
    if not doc_id:
        raise HTTPException(status_code=400, detail="Mã số tài liệu không xác định.")
    
    from src.tasks import compile_document_tectonic
    task = compile_document_tectonic.delay(doc_id, payload.get("tex_content", ""))
    return {"message": "Đã tiếp nhận yêu cầu biên dịch Tectonic vào hàng đợi.", "task_id": task.id}
