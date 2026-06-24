import os

from src.core.infrastructure.redis_client import redis_client
from fastapi import FastAPI, HTTPException, Request
from fastapi.response import JSONResponse
from pydantic import BaseModel

from src.core.infrastructure.configuration import settings

app = FastAPI(title="Background Task Service", version=settings.VERSION)



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=503, content={"detail": "Đã xảy ra lỗi, vui lòng thử lại sau"}
    )


@app.get("/health")
async def read_health():
    await redis_client.get('health')
    return {
        "status": "The background processing service is currently operating normally and ready to accept incoming requests"
    }


@app.post("/documents/compile")
def compile_document(payload: dict):
    doc_id = payload.get("document_id")
    if not doc_id:
        raise HTTPException(
            status_code=400, detail="Thiếu mã tài liệu hợp lệ để biên dịch"
        )

    from src.jobs.task import compile_document_tectonic

    task = compile_document_tectonic.delay(doc_id, payload.get("tex_content", ""))
    return {"message": "Đã thêm tài liệu vào hàng đợi", "task_id": task.id}
