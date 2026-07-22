from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query
from src.schemas.announcement import AnnouncementCreate, AnnouncementSettings
from src.services.announcement import AnnouncementService

from src.core.dependency import get_current_user, get_db
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role, verify_internal_token
from src.repositories.announcement import AnnouncementRepository

router = APIRouter(route_class=LoggingRoute, prefix="/thong-bao")

@router.get("", response_model=APIResponse[Any])
async def get_announcements(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AnnouncementService.get_announcements(
            str(current_user.id), skip, limit, db
        ),
        message="Trích xuất thông báo hoàn tất",
    )

@router.patch("/{notif_id}/doc-hieu", response_model=APIResponse[Any])
async def mark_as_read(
    notif_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AnnouncementService.mark_as_read(notif_id, str(current_user.id), db),
        message="Đã đánh dấu thông báo là đã đọc",
    )

@router.patch("/doc-tat-ca", response_model=APIResponse[Any])
async def mark_all_as_read(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await AnnouncementService.mark_all_as_read(str(current_user.id), db),
        message="Đã đánh dấu tất cả thông báo là đã đọc",
    )

@router.delete("/{notif_id}", response_model=APIResponse[Any])
async def delete_announcement(
    notif_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AnnouncementService.delete_announcement(
            notif_id, str(current_user.id), db
        ),
        message="Xóa thông báo vĩnh viễn hoàn tất",
    )

@router.post("/gui-di", response_model=APIResponse[Any], include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def create_announcement(data: AnnouncementCreate, db=Depends(get_db)):
    return APIResponse(
        data=await AnnouncementService.create_announcement(data, db),
        message="Gửi thông báo hoàn tất",
        status=201,
    )

@router.get("/cai-dat", response_model=APIResponse[Any])
async def get_settings(
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    settings = await AnnouncementRepository.get_settings(str(current_user.id))
    settings = settings or AnnouncementSettings().model_dump()
    return APIResponse(
        data=settings,
        message="Trích xuất cài đặt thông báo hoàn tất",
    )

@router.post("/cai-dat", response_model=APIResponse[Any])
async def update_settings(
    settings: AnnouncementSettings,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    from src.repositories.announcement import AnnouncementRepository
    settings_data = settings.model_dump()
    await AnnouncementRepository.update_settings(str(current_user.id), settings_data)
    return APIResponse(
        data=settings_data,
        message="Cập nhật cài đặt thông báo hoàn tất",
        status=200,
    )
