from typing import Any
from core.dependency import get_db, require_role
from core.response import APIResponse
from core.schemas.user import RoleEnum
from fastapi import APIRouter, Depends
from src.schemas.management import BannerRequest
from src.services.banners import BannerService

router = APIRouter(prefix="/banners")

@router.get("", response_model=APIResponse[Any])
async def get_active_banners(db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.get_banners(active_only=True, db=db),
        message="Active promotional banners have been successfully retrieved and are ready for display",
    )

@router.get("/all", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_all_banners(db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.get_banners(active_only=False, db=db),
        message="Comprehensive list of all promotional banners has been successfully retrieved from system",
    )

@router.post("", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_banner(data: BannerRequest, db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.create_banner(data.model_dump(), db=db),
        message="New promotional banner has been successfully created and added to active rotation",
        status=201,
    )

@router.delete("/{banner_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def delete_banner(banner_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await BannerService.delete_banner(banner_id, db=db),
        message="Specified promotional banner has been permanently removed from the system storage",
    )