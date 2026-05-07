from typing import Any
from shared.core.response import APIResponse
from fastapi import APIRouter, Depends, UploadFile, File
from shared.models.user import UserInDB, RoleEnum
from api.dependency import require_role
from services.storage import StorageService
router = APIRouter(prefix="/luu-trư")
@router.post("/", response_model=APIResponse[Any])
async def upload_asset_to_minio(
    file: UploadFile = File(.),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await StorageService.upload_asset(file, current_user), message="Tải tập tin lên kho lưu trữ thành công.", status=201)
@router.get("/{file_path:path}", response_model=APIResponse[Any])
async def get_presigned_download_url(
    file_path: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    return APIResponse(data=await StorageService.get_presigned_url(file_path), message="Tạo liên kết tải tập tin thành công.", status=200)
