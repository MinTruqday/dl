from typing import Any
from src.core.response import APIResponse
from fastapi import APIRouter, Depends, Request, UploadFile, File
from src.api.dependency import get_current_user, get_db
from src.schemas.user import UserInDB

router = APIRouter(prefix='/dinh-danh')

@router.post('/tro-thanh-tac-gia', response_model=APIResponse[Any])
async def become_author(current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    from src.services.identity import IdentityService
    return APIResponse(data=await IdentityService.become_author(current_user, db=db), message='Nâng cấp lên tác giả thành công')

@router.post('/dang-ky-tac-gia', response_model=APIResponse[Any])
async def apply_author(payload: dict, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    from src.services.identity import IdentityService
    return APIResponse(data=await IdentityService.apply_author(payload, current_user, db=db), message='Gửi yêu cầu trở thành tác giả thành công')

@router.post('/kyc', response_model=APIResponse[Any])
async def upload_kyc(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    from src.services.identity import IdentityService
    return APIResponse(data=await IdentityService.upload_kyc(file, current_user, db=db), message='Tải lên tài liệu KYC thành công')

@router.get('/ho-so/{slug}', response_model=APIResponse[Any])
async def get_public_profile(slug: str, db=Depends(get_db)):
    from src.services.identity import IdentityService
    return APIResponse(data=await IdentityService.get_public_profile(slug, db=db), message='Lấy thông tin hồ sơ thành công')
