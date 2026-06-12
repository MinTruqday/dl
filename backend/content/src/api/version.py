from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from provision.src.schemas.user import UserInDB
from src.api.dependency import get_db, get_current_user
from src.services.version import VersionsService
router = APIRouter(prefix='/phien-ban')

@router.post('/luu/{document_id}', response_model=APIResponse[Any])
async def save_version(document_id: str, version_note: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await VersionsService.save_version(document_id, version_note, current_user, db=db), message='Đã lưu phiên bản tài liệu', status=201)

@router.get('/tai-lieu/{document_id}', response_model=APIResponse[Any])
async def get_document_versions(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await VersionsService.get_versions(document_id, current_user, db=db), message='Đã tải danh sách phiên bản')

@router.post('/{version_id}/khoi-phuc', response_model=APIResponse[Any])
async def restore_version(version_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await VersionsService.restore_version(version_id, current_user, db=db), message='Đã khôi phục phiên bản')