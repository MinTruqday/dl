import os
import redis.asyncio as redis
from core.config import settings
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from src.tasks import compile_document_tectonic

app = FastAPI(title="Background Task Service", version=settings.VERSION)
redis_client = redis.from_url(settings.REDIS_URI, decode_responses=True)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=503,
        content={"detail": "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"}
    )

@app.get("/suc-khoe")
async def check_health():
    await redis_client.ping()
    return {"status": "Kiểm tra sức khỏe hệ thống hoàn tất và ổn định"}

@app.post("/tai-lieu/bien-dich")
def compile_document(payload: dict):
    doc_id = payload.get("document_id")
    if not doc_id:
        raise HTTPException(
            status_code=400,
            detail="Lỗi khi truy xuất tài liệu"
        )

    task = compile_document_tectonic.delay(doc_id, payload.get("tex_content", ""))
    return {
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "task_id": task.id
    }