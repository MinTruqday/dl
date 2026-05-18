from typing import Any
from fastapi import APIRouter, Depends, Query
from api.dependency import require_role
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.archive import ArchiveService
from models.archive import ArchiveUploadRequest

router = APIRouter(prefix="/luu-tru")

@router.get("", response_model=APIResponse[Any])
async def get_my_archives(type: str = Query("all"), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.MODERATOR]))):
    return APIResponse(
        data=await ArchiveService.get_archives(current_user, type),
        message="Lấy danh sách tệp tin thành công"
    )

@router.post("", response_model=APIResponse[Any])
async def upload_archive(data: ArchiveUploadRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.upload_archive(data.model_dump(), current_user),
        message="Tải lên tệp tin thành công",
        status=201
    )

@router.delete("/{archive_id}", response_model=APIResponse[Any])
async def delete_archive(archive_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return APIResponse(
        data=await ArchiveService.delete_archive(archive_id, current_user),
        message="Xóa tệp tin thành công"
    )
