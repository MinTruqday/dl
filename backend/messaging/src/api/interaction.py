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
from src.api.thread import publish_personal_message

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.post("/{message_id}/bay-to-cam-xuc", response_model=APIResponse[Any])
async def add_reaction(
    message_id: str, req: dict, current_user=Depends(get_current_user)
):
    reaction = req.get("reaction")
    result = await InteractionService.add_reaction(message_id, reaction, current_user)
    if not result:
        raise HTTPException(status_code=400, detail="Thao tác tương tác không hợp lệ")
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

@router.post("/{other_user_id}/danh-dau-chua-doc", response_model=APIResponse[Any])
async def mark_unread(other_user_id: str, current_user=Depends(get_current_user)):
    result = await InteractionService.mark_unread(other_user_id, current_user)
    return APIResponse(
        data=result, message="Đánh dấu chưa đọc cuộc trò chuyện hoàn tất"
    )

@router.post("/{other_user_id}/tu-xoa", response_model=APIResponse[Any])
async def set_disappearing_timer(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    timer_seconds = req.get("timer_seconds", 0)
    result = await InteractionService.set_disappearing_timer(other_user_id, timer_seconds, current_user)
    return APIResponse(
        data=result, message="Cấu hình thời gian tự xóa tin nhắn hoàn tất"
    )

@router.post("/cloud/luu-tin-nhan", response_model=APIResponse[Any])
async def save_to_cloud(req: dict, current_user=Depends(get_current_user)):
    msg_id = req.get("message_id", "")
    content = req.get("content", "")
    attachments = req.get("attachments", [])
    result = await InteractionService.save_to_cloud(msg_id, content, attachments, current_user)
    return APIResponse(
        data=result, message="Lưu tin nhắn vào kho cá nhân hoàn tất"
    )

@router.post("/{other_user_id}/chu-de", response_model=APIResponse[Any])
async def update_theme(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    theme_id = req.get("theme_id", "default")
    result = await InteractionService.update_theme(other_user_id, theme_id, current_user)
    return APIResponse(
        data=result, message="Cập nhật chủ đề cuộc trò chuyện thành công"
    )

@router.post("/{message_id}/nhac-hen", response_model=APIResponse[Any])
async def set_message_alarm(message_id: str, req: dict, current_user=Depends(get_current_user)):
    remind_at = req.get("remind_at", "")
    result = await InteractionService.set_message_alarm(message_id, remind_at, current_user)
    return APIResponse(data=result, message="Đặt lịch nhắc hẹn tin nhắn thành công")


@router.post("/{group_id}/chuyen-truong-nhom", response_model=APIResponse[Any])
async def transfer_group_ownership(group_id: str, req: dict, current_user=Depends(get_current_user)):
    new_leader_id = req.get("new_leader_id", "")
    result = await InteractionService.transfer_group_ownership(group_id, new_leader_id, current_user)
    return APIResponse(data=result, message="Chuyển giao quyền Trưởng nhóm thành công")


@router.post("/{group_id}/che-do-cham", response_model=APIResponse[Any])
async def set_group_slow_mode(group_id: str, req: dict, current_user=Depends(get_current_user)):
    delay_seconds = req.get("delay_seconds", 0)
    result = await InteractionService.set_group_slow_mode(group_id, delay_seconds, current_user)
    return APIResponse(data=result, message="Cập nhật chế độ tin nhắn chậm thành công")


@router.get("/{other_user_id}/xuat-lich-su", response_model=APIResponse[Any])
async def export_chat_history(other_user_id: str, current_user=Depends(get_current_user)):
    result = await InteractionService.export_chat_history(other_user_id, current_user)
    return APIResponse(data=result, message="Trích xuất lịch sử trò chuyện hoàn tất")


@router.post("/{other_user_id}/tam-tat-thong-bao", response_model=APIResponse[Any])
async def snooze_notifications(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    minutes = req.get("minutes", 60)
    result = await InteractionService.snooze_notifications(other_user_id, minutes, current_user)
    return APIResponse(data=result, message="Tắt thông báo tạm thời thành công")


@router.get("/{other_user_id}/kho-phuong-tien", response_model=APIResponse[Any])
async def get_media_vault(other_user_id: str, current_user=Depends(get_current_user)):
    result = await InteractionService.get_media_vault(other_user_id, current_user)
    return APIResponse(data=result, message="Trích xuất kho phương tiện & tệp thành công")


@router.delete("/{other_user_id}/don-dung-luong", response_model=APIResponse[Any])
async def clear_chat_storage(other_user_id: str, current_user=Depends(get_current_user)):
    result = await InteractionService.clear_chat_storage(other_user_id, current_user)
    return APIResponse(data=result, message="Dọn dẹp dung lượng lưu trữ cuộc trò chuyện thành công")


@router.post("/{group_id}/thong-bao", response_model=APIResponse[Any])
async def create_announcement(group_id: str, req: dict, current_user=Depends(get_current_user)):
    title = req.get("title", "")
    body = req.get("body", "")
    result = await InteractionService.create_announcement(group_id, title, body, current_user)
    return APIResponse(data=result, message="Đăng thông báo nhóm thành công")



