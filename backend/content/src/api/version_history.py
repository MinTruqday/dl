from typing import Any

from fastapi import APIRouter, Depends
from src.api.system_dependency import get_current_user, get_db
from src.services.version_history import VersionHistory

from core.api_response import APIResponse
from core.system_dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/phien-ban")


@router.post("/luu/{document_id}", response_model=APIResponse[Any])
async def save_version(
    document_id: str,
    version_note: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await VersionHistory.save_version(
            document_id, version_note, current_user, db=db
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
        data=await VersionHistory.get_versions(document_id, current_user, db=db),
        message="Lấy lịch sử phiên bản thành công",
    )


@router.post("/{version_id}/khoi-phuc", response_model=APIResponse[Any])
async def restore_version(
    version_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await VersionHistory.restore_version(version_id, current_user, db=db),
        message="Khôi phục phiên bản lịch sử thành công",
    )
