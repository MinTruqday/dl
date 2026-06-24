from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from src.core.infrastructure.rabbitmq_client import rabbitmq

router = APIRouter()

class PublishRequest(BaseModel):
    queue_name: str
    payload: Dict[str, Any]

class AckRequest(BaseModel):
    delivery_tag: str

@router.post("/xuat-ban")
async def publish_message(request: PublishRequest):
    success = await rabbitmq.publish(request.queue_name, request.payload)
    if not success:
        raise HTTPException(status_code=500, detail="Không thể đẩy tin nhắn vào hàng đợi")
    return {"status": "success", "message": "Tin nhắn đã được đẩy vào hàng đợi"}

@router.get("/tieu-thu/{queue_name}")
async def consume_message(queue_name: str, timeout: int = 30):
    res = await rabbitmq.consume(queue_name, timeout=timeout)
    if res is None:
        return {"data": None}
    return {"data": res}

@router.post("/xac-nhan")
async def ack_message(request: AckRequest):
    success = await rabbitmq.ack_message(request.delivery_tag)
    if not success:
        raise HTTPException(status_code=500, detail="Lỗi xác nhận tin nhắn")
    return {"status": "success"}
