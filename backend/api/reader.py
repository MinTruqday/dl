from typing import Any
from fastapi import APIRouter, Depends, Body
from api.dependencies import get_current_user
from models.user import UserInDB
from core.response import APIResponse
from services.reader import ReaderService
from services.author import AuthorService
from pydantic import BaseModel

router = APIRouter(prefix="/reader")

class PrivacyRequest(BaseModel):
    hide_reading_activity: bool = False
    hide_library: bool = False

class SettingsUpdateRequest(BaseModel):
    settings: dict

class ExcerptShareRequest(BaseModel):
    document_id: str
    text: str
    caption: str = ""

@router.get("/settings/privacy", response_model=APIResponse[Any])
async def get_privacy(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReaderService.get_privacy_settings(current_user), 
        message="Lấy cài đặt quyền riêng tư thành công."
    )

@router.put("/settings/privacy", response_model=APIResponse[Any])
async def update_privacy(data: PrivacyRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReaderService.update_privacy_settings(data.model_dump(), current_user), 
        message="Cập nhật quyền riêng tư thành công."
    )

@router.put("/settings", response_model=APIResponse[Any])
async def update_general_settings(data: SettingsUpdateRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReaderService.update_general_settings(data.settings, current_user), 
        message="Cập nhật cài đặt thành công."
    )

@router.post("/share-excerpt", response_model=APIResponse[Any])
async def share_excerpt(data: ExcerptShareRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReaderService.share_excerpt(data.model_dump(), current_user), 
        message="Chia sẻ trích đoạn thành công.", 
        status=201
    )

@router.post("/apply-author", response_model=APIResponse[Any])
async def apply_author(motivation: str = Body(..., embed=True), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await AuthorService.apply_for_author(motivation, current_user), 
        message="Gửi đơn ứng tuyển thành công.", 
        status=201
    )
