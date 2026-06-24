from typing import Any

from fastapi import APIRouter, Depends, Query
from src.schemas.announcement import AnnouncementCreate
from src.services.announcement import AnnouncementService

from src.core.dependency import get_current_user, get_db
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role
from src.repositories.notification import NotificationRepository

router = APIRouter(prefix="/thong-bao")


@router.get("", response_model=APIResponse[Any])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AnnouncementService.get_notifications(
            str(current_user.id), skip, limit, db
        ),
        message="Lấy thông báo thành công",
    )


@router.patch("/{notif_id}/doc-hieu", response_model=APIResponse[Any])
async def mark_as_read(
    notif_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AnnouncementService.mark_as_read(notif_id, str(current_user.id), db),
        message="Đã đánh dấu thông báo là đã đọc",
    )


@router.patch("/doc-tat-ca", response_model=APIResponse[Any])
async def mark_all_as_read(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await AnnouncementService.mark_all_as_read(str(current_user.id), db),
        message="Đã đánh dấu tất cả thông báo là đã đọc",
    )


@router.delete("/{notif_id}", response_model=APIResponse[Any])
async def delete_notification(
    notif_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AnnouncementService.delete_notification(
            notif_id, str(current_user.id), db
        ),
        message="Xóa thông báo vĩnh viễn thành công",
    )


@router.post("/gui-di", response_model=APIResponse[Any], include_in_schema=False)
async def create_notification(data: AnnouncementCreate, db=Depends(get_db)):
    return APIResponse(
        data=await AnnouncementService.create_notification(data, db),
        message="Gửi thông báo thành công",
        status=201,
    )


@router.post("/cai-dat", response_model=APIResponse[Any])
async def update_settings(
    settings: dict,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    from src.core.repositories.database import NotificationRepository
    await NotificationRepository.update_user_announcement_status(
        {"_id": current_user.id}, 
        {"$set": {"notification_settings": settings}}
    )
    return APIResponse(
        data=settings,
        message="Cập nhật cài đặt thông báo thành công",
        status=200,
    )
