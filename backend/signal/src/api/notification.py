from typing import Any
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from src.api.dependency import get_current_user, get_current_user_from_token, get_db
from src.schemas.notification import NotificationSettingsUpdate, NewsletterRequest
from src.services.notification import NotificationService
from src.core.response import APIResponse

router = APIRouter(prefix='/thong-bao')


@router.get('/dong-du-lieu', response_model=Any)
async def stream_notifications(request: Request, token: str = Query(...), db=Depends(get_db)):
    current_user = await get_current_user_from_token(token)
    return EventSourceResponse(NotificationService.sse_generator(current_user.id, db=db))


@router.get('', response_model=APIResponse[Any])
async def get_notifications(current_user=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await NotificationService.get_notifications(current_user, db=db), message='Lấy danh sách thông báo thành công', status=200)


@router.put('/{notif_id}/da-doc', response_model=APIResponse[Any])
async def mark_notification_read(notif_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await NotificationService.mark_notification_read(notif_id, current_user, db=db), message='Đã đánh dấu thông báo là đã đọc', status=200)


@router.post('/thu-nghiem', response_model=APIResponse[Any])
async def trigger_test_notification(current_user=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await NotificationService.trigger_test_notification(current_user, db=db), message='Gửi thông báo thử nghiệm thành công', status=200)


@router.post('/day-tin', response_model=APIResponse[Any])
async def trigger_push_notif(title: str, body: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await NotificationService.trigger_push_notif(title, body, current_user, db=db), message='Gửi thông báo đẩy thành công', status=200)


@router.get('/cai-dat', response_model=APIResponse[Any])
async def get_notification_settings(current_user=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await NotificationService.get_notification_settings(current_user, db=db), message='Lấy cài đặt thông báo thành công', status=200)


@router.put('/cai-dat', response_model=APIResponse[Any])
async def update_notification_settings(data: NotificationSettingsUpdate, current_user=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await NotificationService.update_notification_settings(data.model_dump(), current_user, db=db), message='Cập nhật cài đặt thông báo thành công', status=200)


@router.post('/danh-dau-tat-ca', response_model=APIResponse[Any])
async def mark_all_read(current_user=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await NotificationService.mark_all_read(current_user, db=db), message='Đã đánh dấu tất cả thông báo là đã đọc', status=200)


@router.post('/ban-tin/dang-ky', response_model=APIResponse[Any])
async def subscribe_newsletter(req: NewsletterRequest, db=Depends(get_db)):
    return APIResponse(data=await NotificationService.subscribe_newsletter(req.email, db=db), message='Đăng ký nhận bản tin thành công', status=201)
