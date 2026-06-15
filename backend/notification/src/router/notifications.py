from typing import Any
from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Query
from src.schemas.notifications import NotificationCreate
from src.services.notifications import NotificationService

router = APIRouter(prefix="/notifications")

@router.get("", response_model=APIResponse[Any])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(
        data=await NotificationService.get_notifications(str(current_user.id), skip, limit),
        message="Requested notifications have been successfully retrieved from the system database records"
    )

@router.patch("/{notification_id}/read", response_model=APIResponse[Any])
async def mark_as_read(
    notification_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(
        data=await NotificationService.mark_as_read(notification_id, str(current_user.id)),
        message="Specified notification has been successfully updated and marked as read by the system"
    )

@router.patch("/read-all", response_model=APIResponse[Any])
async def mark_all_as_read(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await NotificationService.mark_all_as_read(str(current_user.id)),
        message="All pending notifications for the current user have been successfully marked as read"
    )

@router.delete("/{notification_id}", response_model=APIResponse[Any])
async def delete_notification(
    notification_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(
        data=await NotificationService.delete_notification(notification_id, str(current_user.id)),
        message="Specified notification has been permanently removed from the system storage"
    )

@router.post("/dispatch", response_model=APIResponse[Any], include_in_schema=False)
async def create_notification(data: NotificationCreate):
    return APIResponse(
        data=await NotificationService.create_notification(data),
        message="New notification has been successfully generated and dispatched to the intended recipient",
        status=201
    )