from typing import Any, Optional
from fastapi import APIRouter, Depends
from core.dependency import get_db, require_role
from core.schemas.user import RoleEnum
from core.response import APIResponse
from src.services.banner_service import BannerService
from core.schemas.banner import BannerRequest
from pydantic import BaseModel

router = APIRouter(prefix="/quang-cao")


@router.get("", response_model=APIResponse[Any])
async def get_active_banners(db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.get_banners(active_only=True, db=db),
        message="Lấy danh sách biểu ngữ thành công",
    )


@router.get(
    "/tat-ca",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_all_banners(db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.get_banners(active_only=False, db=db),
        message="Lấy toàn bộ danh sách biểu ngữ thành công",
    )


@router.post(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def create_banner(data: BannerRequest, db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.create_banner(data.model_dump(), db=db),
        message="Tạo biểu ngữ thành công",
        status=201,
    )


@router.delete(
    "/{banner_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def delete_banner(banner_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.delete_banner(banner_id, db=db),
        message="Xoá biểu ngữ thành công",
    )
