from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from src.api.dependency import get_current_user, get_db
from src.services.version import VersionService

from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/phien-ban")

@router.post("/luu/{document_id}", response_model=APIResponse[Any])
async def save_version(
    document_id: str,
    version_note: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await VersionService.save_version(
            document_id, version_note, current_user
        ),
        message="Lưu phiên bản lịch sử tài liệu thành công",
        status=201,
    )

@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_document_versions(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await VersionService.get_versions(document_id, current_user),
        message="Lấy lịch sử phiên bản thành công",
    )

@router.post("/{version_id}/khoi-phuc", response_model=APIResponse[Any])
async def restore_version(
    version_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await VersionService.restore_version(version_id, current_user),
        message="Khôi phục phiên bản lịch sử thành công",
    )
