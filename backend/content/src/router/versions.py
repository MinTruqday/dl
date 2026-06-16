from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from core.dependency import get_current_user, get_db
from src.services.versions import VersionService

router = APIRouter(prefix="/phien-lam-cam-quyen")

@router.post("/luu-lai/{document_id}", response_model=APIResponse[Any])
async def save_version(document_id: str, version_note: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await VersionService.save_version(document_id, version_note, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        status=201,
    )

@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_document_versions(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await VersionService.get_versions(document_id, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
    )

@router.post("/{version_id}/khoi-phuc", response_model=APIResponse[Any])
async def restore_version(version_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await VersionService.restore_version(version_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )