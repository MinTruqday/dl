from typing import Any, Optional
from fastapi import APIRouter, Depends
from core.dependency import get_db, require_role
from core.schemas.user import RoleEnum
from core.response import APIResponse
from src.services.banner_service import BannerService
from pydantic import BaseModel

class BannerRequest(BaseModel):
    title: str
    image_url: str
    target_url: Optional[str] = None
    is_active: bool = True

router = APIRouter(prefix="/banners")


@router.get("", response_model=APIResponse[Any])
async def get_active_banners(db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.get_banners(active_only=True, db=db),
        message="The active promotional banners have been successfully retrieved and are ready for display",
    )


@router.get(
    "/all",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_all_banners(db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.get_banners(active_only=False, db=db),
        message="The comprehensive list of all promotional banners has been successfully retrieved from the system",
    )


@router.post(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def create_banner(data: BannerRequest, db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.create_banner(data.model_dump(), db=db),
        message="The new promotional banner has been successfully created and added to the active rotation",
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
        message="The specified promotional banner has been permanently removed from the system",
    )