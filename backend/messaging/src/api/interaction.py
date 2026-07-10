from src.core.infrastructure.redis import redis
import json
from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query
from src.schemas.thread import Conversation, Creation, Response
from src.services.interaction import InteractionService

from src.core.infrastructure.database import database
from src.core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from src.core.dependency import get_current_user
from src.core.response import APIResponse
from src.repositories.message import MessageRepository

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.post("/{message_id}/bay-to-cam-xuc", response_model=APIResponse[Any])
async def add_reaction(
    message_id: str, req: dict, current_user=Depends(get_current_user)
):
    reaction = req.get("reaction")
    result = await InteractionService.add_reaction(message_id, reaction, current_user)
    if not result:
        return APIResponse(message="Thao tác tương tác không hợp lệ", status=400)
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message(
        {"type": "message_reaction", "data": result}, other_id
    )
    return APIResponse(data=result, message="Ghi nhận tương tác tin nhắn hoàn tất")

@router.post("/{other_user_id}/chan", response_model=APIResponse[Any])
async def block_user(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await InteractionService.block_user(other_user_id, current_user),
        message="Thực hiện chặn tài khoản gửi tin nhắn hoàn tất",
    )

@router.post("/{other_user_id}/bo-chan", response_model=APIResponse[Any])
async def unblock_user(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await InteractionService.unblock_user(other_user_id, current_user),
        message="Đã gỡ bỏ giới hạn tương tác",
    )

@router.get("/{other_user_id}/trang-thai-chan", response_model=APIResponse[Any])
async def get_blocked_status(
    other_user_id: str, current_user=Depends(get_current_user)
):
    blocked = await InteractionService.check_blocked_status(
        str(current_user.id), other_user_id
    )
    return APIResponse(
        data={"is_blocked": blocked},
        message="Xác minh trạng thái hạn chế tương tác hoàn tất",
    )

@router.post("/{other_user_id}/tat-thong-bao", response_model=APIResponse[Any])
async def toggle_mute(other_user_id: str, current_user=Depends(get_current_user)):
    result = await InteractionService.toggle_mute(other_user_id, current_user)
    return APIResponse(
        data=result, message="Cập nhật cấu hình thông báo cuộc trò chuyện hoàn tất"
    )

