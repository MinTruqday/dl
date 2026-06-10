from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import get_db, get_current_user
from models.user import UserInDB
from models.highlight import ReadingPreferenceUpdate
from core.response import APIResponse
from services.preference import PreferenceService
router = APIRouter(prefix='/tuy-chinh', tags=['Preference'])

@router.get('', response_model=APIResponse[Any])
async def get_preferences(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PreferenceService.get_preferences(current_user, db=db), message='Lấy cài đặt tùy chỉnh thành công')

@router.put('', response_model=APIResponse[Any])
async def update_preferences(data: ReadingPreferenceUpdate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PreferenceService.update_preferences(data.model_dump(exclude_unset=True), current_user, db=db), message='Cập nhật cài đặt tùy chỉnh thành công')