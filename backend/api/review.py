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
from models.review import ReviewCreate, ReviewResponse
router = APIRouter(prefix='/danh-gia')
(prefix='/danh-gia')

@router.post('/{document_id}', response_model=APIResponse[ReviewResponse])
async def create_document_review(document_id: str, review_in: ReviewCreate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)) -> Any:
    return APIResponse(data=await ReviewService.create_review(document_id, review_in, current_user, db=db), message='Gửi đánh giá tài liệu thành công', status=201)

@router.get('/{document_id}', response_model=APIResponse[List[ReviewResponse]])
async def get_document_reviews(document_id: str, db=Depends(get_db)) -> Any:
    return APIResponse(data=await ReviewService.get_reviews(document_id, db=db), message='Lấy danh sách đánh giá tài liệu thành công', status=200)