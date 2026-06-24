from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from src.core.infrastructure.rabbitmq_client import rabbitmq

router = APIRouter()

class PublishRequest(BaseModel):
    queue_name: str
    payload: Dict[str, Any]

@router.post("/xuat-ban")
async def publish_message(request: PublishRequest):
    success = await rabbitmq.publish(request.queue_name, request.payload)
    if not success:
        raise HTTPException(status_code=500, detail="Không thể đẩy tin nhắn vào hàng đợi")
    return {"status": "success", "message": "Tin nhắn đã được đẩy vào hàng đợi"}

@router.get("/tieu-thu/{queue_name}")
async def consume_message(queue_name: str, timeout: int = 30):
    payload = await rabbitmq.consume(queue_name, timeout=timeout)
    if payload is None:
        return {"data": None}
    return {"data": payload}
