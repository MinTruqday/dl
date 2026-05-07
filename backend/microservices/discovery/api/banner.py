from typing import Any, Optional
from fastapi import APIRouter, Depends
from api.dependency import require_role
from shared.models.user import RoleEnum
from shared.core.response import APIResponse
from services.banner import BannerService
from pydantic import BaseModel
router = APIRouter(prefix="/anh-quang-cao")
class BannerRequest(BaseModel):
    title: str
    image_url: str
    link_url: Optional[str] = None
    priority: int = 0
@router.get("/", response_model=APIResponse[Any])
async def get_active_banners():
    return APIResponse(
        data=await BannerService.get_banners(active_only=True), 
        message="Lấy danh sách banner quảng cáo thành công"
    )
@router.get("/tat-ca", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_all_banners():
    return APIResponse(
        data=await BannerService.get_banners(active_only=False), 
        message="Lấy toàn bộ danh sách banner thành công"
    )
@router.post("/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_banner(data: BannerRequest):
    return APIResponse(
        data=await BannerService.create_banner(data.model_dump()), 
        message="Tạo banner quảng cáo thành công",
        status=201
    )
@router.delete("/{banner_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def delete_banner(banner_id: str):
    return APIResponse(
        data=await BannerService.delete_banner(banner_id), 
        message="Xóa banner thành công"
    )
