from typing import Any
from fastapi import APIRouter, Depends, Query
from api.dependency import require_role
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.asset import AssetService
from pydantic import BaseModel
router = APIRouter(prefix="/tai-nguyen")
class AssetUploadRequest(BaseModel):
    filename: str
    type: str = "image"
    size_bytes: int = 0
    url: str = ""
@router.get("", response_model=APIResponse[Any])
async def get_my_assets(type: str = Query("all"), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.MODERATOR]))):
    return APIResponse(
        data=await AssetService.get_assets(current_user, type),
        message="Lấy danh sách tài nguyên thành công"
    )
@router.post("", response_model=APIResponse[Any])
async def upload_asset(data: AssetUploadRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await AssetService.upload_asset(data.model_dump(), current_user),
        message="Tải lên tài nguyên thành công",
        status=201
    )
@router.delete("/{asset_id}", response_model=APIResponse[Any])
async def delete_asset(asset_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await AssetService.delete_asset(asset_id, current_user),
        message="Xóa tài nguyên thành công"
    )
