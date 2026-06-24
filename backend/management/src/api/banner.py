from typing import Any, Optional

from fastapi import APIRouter, Depends
from src.schemas.banner import BannerRequest
from src.services.banner import BannerService

from src.core.dependency import get_db, require_role
from src.core.response import APIResponse
from src.schemas.account import Role


router = APIRouter(prefix="/quang-cao")


@router.get("", response_model=APIResponse[Any])
async def get_active_banners(db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.get_banners(active_only=True),
        message="Tải banner quảng cáo thành công",
    )


@router.get(
    "/tat-ca",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_all_banners(db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.get_banners(active_only=False),
        message="Lấy danh sách banner quảng cáo thành công",
    )


@router.post(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def create_banner(data: BannerRequest, db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.create_banner(data.model_dump()),
        message="Tạo banner quảng cáo thành công",
        status=201,
    )


@router.delete(
    "/{banner_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def delete_banner(banner_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.delete_banner(banner_id),
        message="Xóa vĩnh viễn banner quảng cáo thành công",
    )
