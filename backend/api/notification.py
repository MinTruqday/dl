from fastapi import APIRouter, Depends, Query, Request
from sse_starlette.sse import EventSourceResponse
from models.user import UserInDB, RoleEnum
from api.dependencies import get_current_user, get_current_user_token_param, require_role, RateLimiter
from services.notification import NotificationService

router = APIRouter()

@router.get("/notifications/stream")
async def stream_notifications(
    request: Request,
    token: str = Query(...),
    _ = Depends(RateLimiter(calls=10, period=60))
):
    current_user = await get_current_user_token_param(token)
    return EventSourceResponse(NotificationService.sse_generator(current_user.id))

@router.get("/notifications")
async def get_notifications(current_user: UserInDB = Depends(get_current_user)):
    return await NotificationService.get_notifications(current_user)

@router.put("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await NotificationService.mark_notification_read(notif_id, current_user)

@router.post("/notifications/trigger_test")
async def trigger_test_notification(current_user: UserInDB = Depends(get_current_user)):
    return await NotificationService.trigger_test_notification(current_user)

@router.post("/notifications/push")
async def trigger_push_notif(title: str, body: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return await NotificationService.trigger_push_notif(title, body, current_user)

from pydantic import BaseModel

class NotificationSettingsUpdate(BaseModel):
    enable_comment_notifications: bool = True
    enable_follow_notifications: bool = True
    enable_mention_notifications: bool = True
    enable_system_notifications: bool = True
    enable_email_digest: bool = False

@router.get("/notifications/settings")
async def get_notification_settings(current_user: UserInDB = Depends(get_current_user)):
    return await NotificationService.get_notification_settings(current_user)

@router.put("/notifications/settings")
async def update_notification_settings(data: NotificationSettingsUpdate, current_user: UserInDB = Depends(get_current_user)):
    return await NotificationService.update_notification_settings(data.model_dump(), current_user)

@router.post("/notifications/mark-all-read")
async def mark_all_read(current_user: UserInDB = Depends(get_current_user)):
    return await NotificationService.mark_all_read(current_user)
