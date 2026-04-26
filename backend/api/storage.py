from fastapi import APIRouter, Depends, UploadFile, File
from models.user import UserInDB, RoleEnum
from api.dependencies import require_role
from services.storage import StorageService

router = APIRouter(prefix="/storage")

@router.post("/")
async def upload_asset_to_minio(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return await StorageService.upload_asset(file, current_user)

@router.get("/{file_path:path}")
async def get_presigned_download_url(
    file_path: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    return await StorageService.get_presigned_url(file_path)
