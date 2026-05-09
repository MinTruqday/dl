from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from models.user import UserInDB
from api.dependency import get_current_user
from services.version import VersionsService

router = APIRouter(prefix="/phien-ban")

@router.post("/luu/{document_id}", response_model=APIResponse[Any])
async def save_version(document_id: str, version_note: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await VersionsService.save_version(document_id, version_note, current_user), message="Lưu phiên bản tài liệu thành công", status=201)

@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_document_versions(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await VersionsService.get_versions(document_id, current_user), message="Lấy danh sách phiên bản thành công")

@router.post("/{version_id}/khoi-phuc", response_model=APIResponse[Any])
async def restore_version(version_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await VersionsService.restore_version(version_id, current_user), message="Khôi phục phiên bản thành công")
