import os
from fastapi import FastAPI, HTTPException
import redis
from pydantic import BaseModel
from src.tasks import convert_and_send_to_kindle
app = FastAPI(title="Hệ thống tác vụ biên dịch AI", version="2.0.26")
redis_client = redis.from_url(os.environ.get("REDIS_URI"))
class KindleRequest(BaseModel):
    document_id: str
    kindle_email: str
    original_format: str
@app.get("/health")
def read_health():
    try:
        redis_client.ping()
        return {"status": "Hệ thống hoạt động bình thường."}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Bạn không thể thực hiện thao tác này ngay lúc này. Vui lòng thử lại sau.")
@app.post("/tasks/tectonic/compile")
def compile_document(payload: dict):
    doc_id = payload.get("document_id")
    if not doc_id:
        raise HTTPException(status_code=400, detail="Mã số tài liệu không xác định.")
    from src.tasks import compile_document_tectonic
    task = compile_document_tectonic.delay(doc_id, payload.get("tex_content", ""))
    return {"message": "Đã tiếp nhận yêu cầu biên dịch Tectonic vào hàng đợi.", "task_id": task.id}
@app.post("/tasks/device/send-to-kindle")
def trigger_send_to_kindle(req: KindleRequest):
    task = convert_and_send_to_kindle.delay(req.document_id, req.kindle_email, req.original_format)
    return {
        "message": "Tài liệu đang được biên dịch ở hệ thống nội vi để truyền đến thiết bị đọc.", 
        "celery_task_id": task.id
    }
