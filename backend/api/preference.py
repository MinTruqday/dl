from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import get_current_user
from models.user import UserInDB
from models.highlight import ReadingPreferenceUpdate
from core.response import APIResponse
from services.preference import PreferenceService

router = APIRouter(prefix="/tuy-chinh", tags=["Preference"])

@router.get("", response_model=APIResponse[Any])
async def get_preferences(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PreferenceService.get_preferences(current_user),
        message="Lấy cài đặt tùy chỉnh thành công"
    )

@router.put("", response_model=APIResponse[Any])
async def update_preferences(data: ReadingPreferenceUpdate, current_user: UserInDB = Depends(get_current_user)):
    # Note: ReadingPreferenceUpdate should handle both typography and theme fields
    return APIResponse(
        data=await PreferenceService.update_preferences(data.model_dump(), current_user),
        message="Cập nhật cài đặt tùy chỉnh thành công"
    )
