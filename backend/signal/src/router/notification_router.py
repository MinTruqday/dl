from typing import Any

from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Query
from src.schemas.notification_schema import NotificationCreate
from src.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications")


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
        message="The requested notifications have been successfully retrieved from the system records",
    )


@router.patch("/{notif_id}/read", response_model=APIResponse[Any])
async def mark_as_read(
    notif_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await NotificationService.mark_as_read(notif_id, str(current_user.id), db),
        message="The specified notification has been successfully updated and marked as read by the system",
    )


@router.patch("/read-all", response_model=APIResponse[Any])
async def mark_all_as_read(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await NotificationService.mark_all_as_read(str(current_user.id), db),
        message="All pending notifications for the current user have been successfully marked as read",
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
        message="The specified notification has been permanently removed from the system",
    )


@router.post("/dispatch", response_model=APIResponse[Any], include_in_schema=False)
async def create_notification(data: NotificationCreate, db=Depends(get_db)):
    return APIResponse(
        data=await NotificationService.create_notification(data, db),
        message="The new notification has been successfully generated and dispatched to the intended recipient",
        status=201,
    )