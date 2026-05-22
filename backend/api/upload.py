from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, UploadFile, File
from models.user import UserInDB, RoleEnum
from api.dependency import require_role
from services.upload import UploadService

router = APIRouter(prefix="/tai-len")

@router.post("/hinh-anh", response_model=APIResponse[Any])
async def upload_image(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await UploadService.upload_image(file), message="Tải hình ảnh lên thành công", status=201)

@router.post("/tai-lieu", response_model=APIResponse[Any])
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await UploadService.upload_document(file), message="Tải tài liệu lên thành công", status=201)

@router.post("/tap-tin", response_model=APIResponse[Any])
async def upload_asset(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(require_role([RoleEnum.READER, RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    from fastapi import HTTPException
    from services.storage import StorageService
    quota = await StorageService.get_storage_quota(current_user.id)
    # Estimate size (file.size might not be populated until read, but for FastAPI UploadFile we can check later)
    # However, to be safe, just check if already exceeded:
    if quota["used"] >= quota["limit"]:
        raise HTTPException(status_code=400, detail="Đã vượt quá hạn mức lưu trữ (1GB). Vui lòng dọn dẹp bớt tệp tin.")
        
    return APIResponse(data=await UploadService.upload_document(file), message="Tải tập tin lên thành công", status=201)

@router.get("/luu-tru/{file_path:path}", response_model=APIResponse[Any])
async def get_presigned_download_url(
    file_path: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.READER]))
):
    return APIResponse(data=await UploadService.get_presigned_url(file_path), message="Tạo liên kết tải tập tin thành công", status=200)
