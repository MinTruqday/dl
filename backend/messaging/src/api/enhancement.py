from src.core.infrastructure.redis import redis
import json
from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query
from src.schemas.thread import Conversation, Creation, Response
from src.services.enhancement import EnhancementService

from src.core.infrastructure.database import database
from src.core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from src.core.dependency import get_current_user, oauth2_scheme
from src.core.response import APIResponse
from src.repositories.message import MessageRepository
from src.api.thread import publish_personal_message

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.post("/{message_id}/dich-thuat", response_model=APIResponse[Any])
async def translate_message(
    message_id: str,
    req: dict,
    current_user=Depends(get_current_user),
    bearer_token: str = Depends(oauth2_scheme),
):
    target_lang = req.get("target_lang", "vi")
    result = await EnhancementService.translate_message(
        message_id, target_lang, current_user, bearer_token
    )
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin nhắn cần dịch")
    await publish_personal_message(
        {
            "type": "message_translated",
            "data": {**result, "message_id": message_id},
        },
        str(current_user.id),
    )
    return APIResponse(data=result, message="Dịch văn bản hoàn tất")

@router.post("/{other_user_id}/tu-huy", response_model=APIResponse[Any])
async def toggle_self_destruct(
    other_user_id: str, req: dict, current_user=Depends(get_current_user)
):
    seconds = req.get("seconds", 0)
    result = await EnhancementService.toggle_self_destruct(
        other_user_id, seconds, current_user
    )
    await publish_personal_message(
        {
            "type": "conversation_settings_updated",
            "data": {"self_destruct_seconds": seconds},
        },
        other_user_id,
    )
    return APIResponse(data=result, message="Kích hoạt tính năng tự động hủy tin nhắn hoàn tất")

@router.get("/{other_user_id}/goi-y-tra-loi", response_model=APIResponse[Any])
async def get_quick_replies(
    other_user_id: str,
    current_user=Depends(get_current_user),
    bearer_token: str = Depends(oauth2_scheme),
):
    if not current_user.has_ai_access():
        raise HTTPException(
            status_code=403,
            detail="Tính năng gợi ý trả lời thông minh yêu cầu gói Chuyên sâu hoặc Toàn năng",
        )


    
    cache_key = f"quick_replies:{current_user.id}:{other_user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return APIResponse(data=json.loads(cached), message="Trích xuất gợi ý trả lời hoàn tất")
        
    result = await EnhancementService.generate_quick_replies(
        other_user_id, current_user, bearer_token
    )
    
    await redis.setex(cache_key, 10, json.dumps(result))
    
    return APIResponse(data=result, message="Khởi tạo gợi ý trả lời hoàn tất")


@router.post("/{group_id}/link-moi", response_model=APIResponse[Any])
async def generate_group_invite(group_id: str, current_user=Depends(get_current_user)):
    result = await EnhancementService.generate_group_invite(group_id, current_user)
    return APIResponse(data=result, message="Khởi tạo đường dẫn mời tham gia nhóm hoàn tất")


@router.post("/nhom/tham-gia", response_model=APIResponse[Any])
async def join_by_invite(req: dict, current_user=Depends(get_current_user)):
    invite_code = req.get("invite_code", "")
    result = await EnhancementService.join_by_invite(invite_code, current_user)
    return APIResponse(data=result, message="Tham gia nhóm trò chuyện thành công")


@router.post("/{other_user_id}/biet-danh", response_model=APIResponse[Any])
async def set_nickname(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    nickname = req.get("nickname", "")
    result = await EnhancementService.set_nickname(other_user_id, nickname, current_user)
    return APIResponse(data=result, message="Cập nhật biệt danh hoàn tất")


@router.post("/{other_user_id}/danh-thiep", response_model=APIResponse[Any])
async def share_contact_card(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    contact_user_id = req.get("contact_user_id", "")
    result = await EnhancementService.share_contact_card(other_user_id, contact_user_id, current_user)
    return APIResponse(data=result, message="Chia sẻ thẻ danh thiếp thành công")


@router.post("/{other_user_id}/luu-tru", response_model=APIResponse[Any])
async def archive_thread(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    is_archived = req.get("is_archived", True)
    result = await EnhancementService.archive_thread(other_user_id, is_archived, current_user)
    return APIResponse(data=result, message="Cập nhật trạng thái lưu trữ cuộc trò chuyện thành công")


@router.post("/ca-nhan/tra-loi-tu-dong", response_model=APIResponse[Any])
async def set_auto_reply(req: dict, current_user=Depends(get_current_user)):
    auto_reply_text = req.get("auto_reply_text", "")
    is_enabled = req.get("is_enabled", True)
    result = await EnhancementService.set_auto_reply(auto_reply_text, is_enabled, current_user)
    return APIResponse(data=result, message="Cấu hình tin nhắn tự động thành công")


@router.post("/{group_id}/quyen-gui-tin-nhan", response_model=APIResponse[Any])
async def manage_group_permissions(group_id: str, req: dict, current_user=Depends(get_current_user)):
    admin_only = req.get("admin_only", False)
    result = await EnhancementService.manage_group_permissions(group_id, admin_only, current_user)
    return APIResponse(data=result, message="Phân quyền gửi tin nhắn nhóm thành công")


@router.post("/{group_id}/su-kien", response_model=APIResponse[Any])
async def create_group_event(group_id: str, req: dict, current_user=Depends(get_current_user)):
    title = req.get("title", "")
    event_time = req.get("event_time", "")
    result = await EnhancementService.create_group_event(group_id, title, event_time, current_user)
    return APIResponse(data=result, message="Tạo sự kiện nhóm thành công")


@router.post("/{other_user_id}/uu-tien-vip", response_model=APIResponse[Any])
async def set_vip_priority(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    is_vip = req.get("is_vip", True)
    result = await EnhancementService.set_vip_priority(other_user_id, is_vip, current_user)
    return APIResponse(data=result, message="Cập nhật thẻ ưu tiên VIP cuộc trò chuyện thành công")

