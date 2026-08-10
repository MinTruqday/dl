from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.thread import publish_personal_message
from src.core.dependency import get_current_user
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.services.pin import PinService

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")


@router.post("/{message_id}/ghim", response_model=APIResponse[Any])
async def toggle_pin(message_id: str, current_user=Depends(get_current_user)):
    result = await PinService.toggle_pin(message_id, current_user)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy tin nhắn hoặc không có quyền sửa",
        )
    if result == "limit_reached":
        raise HTTPException(
            status_code=400,
            detail="Vượt quá giới hạn số lượng tin nhắn ghim",
        )
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message({"type": "message_pinned", "data": result}, other_id)
    return APIResponse(
        data=result["is_pinned"],
        message="Cập nhật trạng thái ghim tin nhắn hoàn tất",
        status=200,
    )


@router.post("/cuoc-tro-chuyen/{other_user_id}/ghim", response_model=APIResponse[Any])
async def toggle_pin_conversation(
    other_user_id: str, current_user=Depends(get_current_user)
):
    return APIResponse(
        data=await PinService.toggle_pin_conversation(other_user_id, current_user),
        message="Cập nhật ưu tiên cuộc trò chuyện hoàn tất",
    )


@router.get("/{other_user_id}/tin-nhan-ghim", response_model=APIResponse[Any])
async def get_pinned_messages(
    other_user_id: str, current_user=Depends(get_current_user)
):
    result = await PinService.get_pinned_messages(other_user_id, current_user)
    return APIResponse(
        data=result,
        message="Trích xuất danh sách tin nhắn ghim hoàn tất",
    )

