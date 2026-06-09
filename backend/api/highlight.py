from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, WebSocket, WebSocketDisconnect
from core.response import APIResponse
from api.dependency import get_current_user, require_role
from models.user import UserInDB, RoleEnum
from core.config import settings
import httpx
import websockets
import asyncio

CONTENT_URL = settings.CONTENT_SERVICE_URL
CONTENT_WS_URL = CONTENT_URL.replace("http://", "ws://").replace("https://", "wss://")

async def _proxy(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.request(method, f"{CONTENT_URL}{path}", **kwargs)
            if res.status_code >= 400:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi"))
            return res.json()
        except HTTPException:
            raise
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Lỗi kết nối Content Service: {e}")

from models.user import UserInDB
from models.highlight import HighlightCreateRequest, HighlightNoteUpdateRequest, ReadingPreferenceUpdate
router = APIRouter(prefix='/neu-bat')
(prefix='/neu-bat')

@router.post('/tai-lieu/{document_id}', response_model=APIResponse[Any])
async def create_highlight(document_id: str, data: HighlightCreateRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await HighlightService.create_highlight(document_id, data.model_dump(), current_user, db=db), message='Tạo nêu bật đoạn văn thành công', status=201)

@router.get('/tai-lieu/{document_id}', response_model=APIResponse[Any])
async def get_highlights(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await HighlightService.get_highlights(document_id, current_user, db=db), message='Lấy danh sách nêu bật của tài liệu thành công', status=200)

@router.put('/{highlight_id}/ghi-chu', response_model=APIResponse[Any])
async def update_highlight_note(highlight_id: str, data: HighlightNoteUpdateRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await HighlightService.update_highlight_note(highlight_id, data.note, current_user, db=db), message='Cập nhật ghi chú nêu bật thành công', status=200)

@router.delete('/{highlight_id}', response_model=APIResponse[Any])
async def delete_highlight(highlight_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await HighlightService.delete_highlight(highlight_id, current_user, db=db), message='Xóa nêu bật đoạn văn thành công', status=200)

@router.get('/ghi-chu', response_model=APIResponse[Any])
async def get_all_notes(cursor: str=Query(None), limit: int=Query(50, ge=1, le=200), skip: int=Query(0, ge=0), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await HighlightService.get_all_notes(current_user, cursor, limit, skip, db=db), message='Lấy danh sách ghi chú thành công', status=200)

@router.get('/tai-lieu/{document_id}/xuat-tai-lieu', response_model=APIResponse[Any])
async def export_highlights_markdown(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await HighlightService.export_highlights_markdown(document_id, current_user, db=db), message='Xuất bản danh sách nêu bật (Markdown) thành công', status=200)