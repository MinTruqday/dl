from typing import Any, Optional

from fastapi import APIRouter, Depends
from src.schemas.promotional_banner import BannerRequest
from src.services.banner import PromotionalBanner

from core.dependency import get_db, require_role
from core.response import APIResponse
from src.schemas.user_identity_profile import RoleEnum


router = APIRouter(prefix="/quang-cao")


@router.get("", response_model=APIResponse[Any])
async def get_active_banners(db=Depends(get_db)):
    return APIResponse(
        data=await PromotionalBanner.get_banners(active_only=True, db=db),
        message="Tải banner quảng cáo thành công",
    )


@router.get(
    "/tat-ca",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_all_banners(db=Depends(get_db)):
    return APIResponse(
        data=await PromotionalBanner.get_banners(active_only=False, db=db),
        message="Lấy danh sách banner quảng cáo thành công",
    )


@router.post(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def create_banner(data: BannerRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PromotionalBanner.create_banner(data.model_dump(), db=db),
        message="Tạo banner quảng cáo thành công",
        status=201,
    )


@router.delete(
    "/{banner_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def delete_banner(banner_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await PromotionalBanner.delete_banner(banner_id, db=db),
        message="Xóa vĩnh viễn banner quảng cáo thành công",
    )
