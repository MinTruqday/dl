from typing import Any

from fastapi import APIRouter, Depends, Query
from src.schemas.push_notification import NotificationCreate
from src.services.push_notification import PushNotification

from shared.dependencies import get_current_user, get_db
from shared.responses import APIResponse
from shared.dependencies import CurrentUser, RoleEnum

router = APIRouter(prefix="/thong-bao")


@router.get("", response_model=APIResponse[Any])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PushNotification.get_notifications(
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
        data=await PushNotification.mark_as_read(notif_id, str(current_user.id), db),
        message="Đã đánh dấu thông báo là đã đọc",
    )


@router.patch("/doc-tat-ca", response_model=APIResponse[Any])
async def mark_all_as_read(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await PushNotification.mark_all_as_read(str(current_user.id), db),
        message="Đã đánh dấu tất cả thông báo là đã đọc",
    )


@router.delete("/{notif_id}", response_model=APIResponse[Any])
async def delete_notification(
    notif_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PushNotification.delete_notification(
            notif_id, str(current_user.id), db
        ),
        message="Xóa thông báo vĩnh viễn thành công",
    )


@router.post("/gui-di", response_model=APIResponse[Any], include_in_schema=False)
async def create_notification(data: NotificationCreate, db=Depends(get_db)):
    return APIResponse(
        data=await PushNotification.create_notification(data, db),
        message="Gửi thông báo thành công",
        status=201,
    )


@router.post("/cai-dat", response_model=APIResponse[Any])
async def update_settings(
    settings: dict,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    from shared.repositories.base_repository import RepositoryFactory
    await RepositoryFactory.get("users").update_one(
        {"_id": current_user.id}, 
        {"$set": {"notification_settings": settings}}
    )
    return APIResponse(
        data=settings,
        message="Cập nhật cài đặt thông báo thành công",
        status=200,
    )
