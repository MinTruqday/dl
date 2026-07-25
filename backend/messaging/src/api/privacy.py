from typing import Any
from fastapi import APIRouter
from src.core.logging_route import LoggingRoute
from src.core.dependency import Depends, get_current_user
from src.core.response import APIResponse
from src.services.privacy import PrivacyService
from src.api.thread import publish_personal_message

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.post("/{other_user_id}/tu-huy", response_model=APIResponse[Any])
async def toggle_self_destruct(
    other_user_id: str, req: dict, current_user=Depends(get_current_user)
):
    seconds = req.get("seconds", 0)
    result = await PrivacyService.toggle_self_destruct(
        other_user_id, seconds, current_user
    )
    await publish_personal_message(
        {
            "type": "conversation_settings_updated",
            "data": {"self_destruct_seconds": seconds},
        },
        other_user_id,
    )
    return APIResponse(
        data=result, message="Kích hoạt tính năng tự động hủy tin nhắn hoàn tất"
    )

@router.post("/{other_user_id}/xoa-dinh-ky", response_model=APIResponse[Any])
async def set_auto_clean_schedule(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    days = req.get("days", 30)
    result = await PrivacyService.set_auto_clean_schedule(other_user_id, days, current_user)
    return APIResponse(data=result, message="Cấu hình lịch xóa định kỳ cuộc trò chuyện thành công")
