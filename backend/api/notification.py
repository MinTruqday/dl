from typing import Any
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import StreamingResponse
from api.dependency import get_current_user
from core.response import APIResponse
from core.config import settings
from models.user import UserInDB, NotificationSettingsUpdate
from pydantic import BaseModel
import httpx

SIGNAL_URL = settings.SIGNAL_SERVICE_URL
router = APIRouter(prefix='/thong-bao')


class NewsletterRequest(BaseModel):
    email: str


async def _proxy(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.request(method, f"{SIGNAL_URL}{path}", **kwargs)
            if res.status_code >= 400:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi thông báo"))
            return res.json()
        except HTTPException:
            raise
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không thể kết nối đến Signal Service: {e}")


@router.get('/dong-du-lieu')
async def stream_notifications(request: Request, token: str = Query(...)):
    """Proxy SSE stream từ Signal Service về client."""
    async def event_stream():
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream("GET", f"{SIGNAL_URL}/thong-bao/dong-du-lieu", params={"token": token}) as res:
                    async for chunk in res.aiter_text():
                        if await request.is_disconnected():
                            break
                        yield chunk
            except Exception:
                pass

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get('', response_model=APIResponse[Any])
async def get_notifications(current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("GET", "/thong-bao", headers={"X-User-Id": str(current_user.id)})


@router.put('/{notif_id}/da-doc', response_model=APIResponse[Any])
async def mark_notification_read(notif_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("PUT", f"/thong-bao/{notif_id}/da-doc", headers={"X-User-Id": str(current_user.id)})


@router.post('/thu-nghiem', response_model=APIResponse[Any])
async def trigger_test_notification(current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", "/thong-bao/thu-nghiem", headers={"X-User-Id": str(current_user.id)})


@router.post('/day-tin', response_model=APIResponse[Any])
async def trigger_push_notif(title: str, body: str, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", "/thong-bao/day-tin", params={"title": title, "body": body}, headers={"X-User-Id": str(current_user.id)})


@router.get('/cai-dat', response_model=APIResponse[Any])
async def get_notification_settings(current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("GET", "/thong-bao/cai-dat", headers={"X-User-Id": str(current_user.id)})


@router.put('/cai-dat', response_model=APIResponse[Any])
async def update_notification_settings(data: NotificationSettingsUpdate, current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("PUT", "/thong-bao/cai-dat", json=data.model_dump(), headers={"X-User-Id": str(current_user.id)})


@router.post('/danh-dau-tat-ca', response_model=APIResponse[Any])
async def mark_all_read(current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", "/thong-bao/danh-dau-tat-ca", headers={"X-User-Id": str(current_user.id)})


@router.post('/ban-tin/dang-ky', response_model=APIResponse[Any])
async def subscribe_newsletter(req: NewsletterRequest):
    return await _proxy("POST", "/thong-bao/ban-tin/dang-ky", json=req.model_dump())