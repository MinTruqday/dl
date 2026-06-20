from typing import Any

from fastapi import APIRouter, Depends
from src.router.dependency import get_current_user, get_db
from src.services.version import VersionsService

from core.response import APIResponse
from core.schemas.user import UserInDB

router = APIRouter(prefix="/versions")


@router.post("/save/{document_id}", response_model=APIResponse[Any])
async def save_version(
    document_id: str,
    version_note: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await VersionsService.save_version(
            document_id, version_note, current_user, db=db
        ),
        message="Lưu phiên bản lịch sử tài liệu thành công",
        status=201,
    )


@router.get("/documents/{document_id}", response_model=APIResponse[Any])
async def get_document_versions(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await VersionsService.get_versions(document_id, current_user, db=db),
        message="Lấy lịch sử phiên bản thành công",
    )


@router.post("/{version_id}/restore", response_model=APIResponse[Any])
async def restore_version(
    version_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await VersionsService.restore_version(version_id, current_user, db=db),
        message="Khôi phục phiên bản lịch sử thành công",
    )
