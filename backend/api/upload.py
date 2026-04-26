from fastapi import APIRouter, Depends, UploadFile, File
from models.user import UserInDB, RoleEnum
from api.dependencies import require_role
from services.upload import UploadService
from typing import Any

router = APIRouter(prefix="/upload")

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return await UploadService.upload_image(file)

@router.get("/storage/{file_path:path}")
async def get_presigned_download_url(
    file_path: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER, RoleEnum.GUEST]))
):
    return await UploadService.get_presigned_url(file_path)
