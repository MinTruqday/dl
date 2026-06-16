from typing import Any
from core.dependency import get_current_user, get_db
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from src.schemas.notifications import NotificationCreate
from src.services.notifications import NotificationService

router = APIRouter(prefix="/thong-bao")

@router.get("", response_model=APIResponse[Any])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    return APIResponse(
        data=await NotificationService.get_notifications(str(current_user.get("id")), skip, limit),
        message="Yêu cầu đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.patch("/{notification_id}/doc-hieu", response_model=APIResponse[Any])
async def mark_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    return APIResponse(
        data=await NotificationService.mark_as_read(notification_id, str(current_user.get("id"))),
        message="Yêu cầu đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.patch("/doc-hieu-tat-ca", response_model=APIResponse[Any])
async def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    return APIResponse(
        data=await NotificationService.mark_all_as_read(str(current_user.get("id"))),
        message="Yêu cầu đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.delete("/{notification_id}", response_model=APIResponse[Any])
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    return APIResponse(
        data=await NotificationService.delete_notification(notification_id, str(current_user.get("id"))),
        message="Lỗi truy xuất cơ sở dữ liệu hệ thống"
    )

@router.post("/gui-di", response_model=APIResponse[Any], include_in_schema=False)
async def create_notification(data: NotificationCreate):
    return APIResponse(
        data=await NotificationService.create_notification(data),
        message="Yêu cầu đã được hệ thống tiếp nhận và xử lý thành công",
        status=201
    )