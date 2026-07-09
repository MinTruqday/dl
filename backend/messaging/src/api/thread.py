from src.core.infrastructure.redis import redis
import json
from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query
from src.schemas.thread import Conversation, Creation, Response
from src.services.thread import ThreadService

from src.core.infrastructure.database import database
from src.core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from src.core.dependency import get_current_user
from src.core.response import APIResponse
from src.repositories.message import MessageRepository

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

async def publish_personal_message(message: dict, receiver_id: str):
    import json

    from fastapi.encoders import jsonable_encoder

    payload = json.dumps(jsonable_encoder(message))
    
    targets = [receiver_id]
    if receiver_id.startswith("group_"):
        group = await MessageRepository.find_group(
            {"_id": receiver_id}
        )
        if group:
            targets = group.get("members", [])
    for target_id in targets:
        await redis.publish(f"message_delivery:{target_id}", payload)

@router.post("/", response_model=APIResponse[Any])
async def send_message(req: Creation, current_user=Depends(get_current_user)):
    msg = await ThreadService.send_message(
        req.receiver_id,
        req.content,
        current_user,
        req.image_url,
        req.reply_to_id,
        req.audio_url,
        req.client_msg_id,
        req.attachments,
    )
    await publish_personal_message(
        {"type": "new_message", "data": msg}, req.receiver_id
    )
    return APIResponse(
        data=msg, message="Gửi tin nhắn trực tiếp thành công", status=201
    )

@router.get("/{other_user_id}", response_model=APIResponse[Any])
async def get_messages(
    other_user_id: str,
    cursor: str = None,
    limit: int = Query(500),
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await ThreadService.get_messages(
            other_user_id, current_user, limit, cursor
        ),
        message="Lấy lịch sử cuộc trò chuyện thành công",
        status=200,
    )

@router.put("/{message_id}", response_model=APIResponse[Any])
async def edit_message(
    message_id: str, req: dict, current_user=Depends(get_current_user)
):
    content = req.get("content")
    if not content:
        return APIResponse(message="Nội dung tin nhắn không được để trống", status=400)
    result = await ThreadService.edit_message(message_id, content, current_user)
    if not result:
        return APIResponse(message="Không thể chỉnh sửa tin nhắn", status=403)
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message({"type": "message_edited", "data": result}, other_id)
    return APIResponse(
        data=result, message="Cập nhật nội dung tin nhắn thành công", status=200
    )

@router.delete("/{message_id}", response_model=APIResponse[Any])
async def recall_message(message_id: str, current_user=Depends(get_current_user)):
    result = await ThreadService.recall_message(message_id, current_user)
    if not result:
        return APIResponse(message="Không có quyền thu hồi tin nhắn", status=403)
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message(
        {"type": "message_recalled", "data": result}, other_id
    )
    return APIResponse(data=result, message="Thu hồi tin nhắn thành công", status=200)

@router.get("/{other_user_id}/tim-kiem", response_model=APIResponse[Any])
async def search_messages(
    other_user_id: str, q: str = Query(...), current_user=Depends(get_current_user)
):
    return APIResponse(
        data=await ThreadService.search_messages(other_user_id, q, current_user),
        message="Tìm kiếm tin nhắn thành công",
    )

