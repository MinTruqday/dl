from src.core.infrastructure.redis import redis
from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query
from src.schemas.thread import Creation
from src.services.thread import ThreadService

from src.core.dependency import Depends
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

@router.post("/", response_model=APIResponse[Any], status_code=201)
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
        req.parent_message_id,
        req.scheduled_at,
    )
    if not msg.get("is_scheduled"):
        await publish_personal_message(
            {"type": "new_message", "data": msg}, req.receiver_id
        )
    else:
        await publish_personal_message(
            {"type": "scheduled_message", "data": msg}, current_user.id
        )
    return APIResponse(
        data=msg, message="Gửi tin nhắn trực tiếp hoàn tất", status=201
    )

@router.get("/{other_user_id}", response_model=APIResponse[Any])
async def get_messages(
    other_user_id: str,
    cursor: str = None,
    limit: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await ThreadService.get_messages(
            other_user_id, current_user, limit, cursor
        ),
        message="Trích xuất lịch sử cuộc trò chuyện hoàn tất",
        status=200,
    )

@router.get("/{message_id}/thread", response_model=APIResponse[Any])
async def get_thread_replies(
    message_id: str,
    cursor: str = None,
    limit: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await ThreadService.get_thread_replies(
            message_id, current_user, limit, cursor
        ),
        message="Trích xuất luồng tin nhắn hoàn tất",
        status=200,
    )

@router.put("/{message_id}", response_model=APIResponse[Any])
async def edit_message(
    message_id: str, req: dict, current_user=Depends(get_current_user)
):
    content = req.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Nội dung tin nhắn không được để trống")
    result = await ThreadService.edit_message(message_id, content, current_user)
    if not result:
        raise HTTPException(status_code=403, detail="Không thể chỉnh sửa tin nhắn")
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message({"type": "message_edited", "data": result}, other_id)
    return APIResponse(
        data=result, message="Cập nhật nội dung tin nhắn hoàn tất", status=200
    )

@router.delete("/{message_id}", response_model=APIResponse[Any])
async def recall_message(message_id: str, current_user=Depends(get_current_user)):
    result = await ThreadService.recall_message(message_id, current_user)
    if not result:
        raise HTTPException(status_code=403, detail="Không có quyền thu hồi tin nhắn")
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message(
        {"type": "message_recalled", "data": result}, other_id
    )
    return APIResponse(data=result, message="Thu hồi tin nhắn hoàn tất", status=200)

@router.get("/{other_user_id}/tim-kiem", response_model=APIResponse[Any])
async def search_messages(
    other_user_id: str, q: str, current_user=Depends(get_current_user)
):
    return APIResponse(
        data=await ThreadService.search_messages(other_user_id, q, current_user),
        message="Tìm kiếm tin nhắn hoàn tất",
    )

@router.post("/chuyen-tiep", response_model=APIResponse[Any])
async def forward_message(req: dict, current_user=Depends(get_current_user)):
    message_id = req.get("message_id")
    receiver_ids = req.get("receiver_ids", [])
    if not message_id or not receiver_ids or len(receiver_ids) > 20:
        raise HTTPException(status_code=400, detail="Dữ liệu chuyển tiếp không hợp lệ")
    
    result = await ThreadService.forward_message(message_id, receiver_ids, current_user)
    for msg in result.get("messages", []):
        await publish_personal_message(
            {"type": "new_message", "data": msg}, msg["receiver_id"]
        )
    return APIResponse(data=result, message="Chuyển tiếp tin nhắn hoàn tất")

@router.post("/binh-chon", response_model=APIResponse[Any], status_code=201)
async def create_poll(req: dict, current_user=Depends(get_current_user)):
    receiver_id = req.get("receiver_id")
    question = req.get("question")
    options = req.get("options", [])
    if not receiver_id or not isinstance(question, str) or not question.strip() or not 2 <= len(options) <= 10:
        raise HTTPException(status_code=400, detail="Dữ liệu bình chọn không hợp lệ")
        
    msg = await ThreadService.create_poll(receiver_id, question, options, current_user)
    await publish_personal_message(
        {"type": "new_message", "data": msg}, receiver_id
    )
    return APIResponse(data=msg, message="Tạo bình chọn hoàn tất", status=201)

@router.post("/binh-chon/{message_id}/bo-phieu", response_model=APIResponse[Any])
async def vote_poll(message_id: str, req: dict, current_user=Depends(get_current_user)):
    option_id = req.get("option_id")
    if not option_id:
        raise HTTPException(status_code=400, detail="Lựa chọn không hợp lệ")
        
    result = await ThreadService.vote_poll(message_id, option_id, current_user)
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message({"type": "message_edited", "data": result}, other_id)
    return APIResponse(data=result, message="Bỏ phiếu hoàn tất")


@router.delete("/{message_id}/xoa-phia-toi", response_model=APIResponse[Any])
async def delete_for_me(message_id: str, current_user=Depends(get_current_user)):
    result = await ThreadService.delete_for_me(message_id, current_user)
    return APIResponse(data=result, message="Xóa tin nhắn phía tôi thành công")


@router.post("/{message_id}/khoi-phuc", response_model=APIResponse[Any])
async def restore_message(message_id: str, current_user=Depends(get_current_user)):
    result = await ThreadService.restore_message(message_id, current_user)
    return APIResponse(data=result, message="Khôi phục tin nhắn thành công")
