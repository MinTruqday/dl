from typing import Any

from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Query
from src.schemas.notification import NotificationCreate
from src.services.notification import NotificationService

router = APIRouter(prefix="/thong-bao")


@router.get("", response_model=APIResponse[Any])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await NotificationService.get_notifications(
            str(current_user.id), skip, limit, db
        ),
        message="Đã tải danh sách thông báo",
    )


@router.patch("/{notif_id}/da-doc", response_model=APIResponse[Any])
async def mark_as_read(
    notif_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await NotificationService.mark_as_read(notif_id, str(current_user.id), db),
        message="Đã đánh dấu đã xem",
    )


@router.patch("/da-doc-tat-ca", response_model=APIResponse[Any])
async def mark_all_as_read(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await NotificationService.mark_all_as_read(str(current_user.id), db),
        message="Đã đánh dấu xem tất cả",
    )


@router.delete("/{notif_id}", response_model=APIResponse[Any])
async def delete_notification(
    notif_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await NotificationService.delete_notification(
            notif_id, str(current_user.id), db
        ),
        message="Đã xóa thông báo",
    )


@router.post(
    "/noi-bo/kich-hoat", response_model=APIResponse[Any], include_in_schema=False
)
async def create_notification(data: NotificationCreate, db=Depends(get_db)):
    return APIResponse(
        data=await NotificationService.create_notification(data, db),
        message="Đã tạo thông báo",
        status=201,
    )
