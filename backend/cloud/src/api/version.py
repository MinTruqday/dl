from typing import Any
from fastapi import APIRouter, Body, Depends
from src.api.dependency import require_role
from src.core.dependency import CurrentUser, Role
from src.core.response import APIResponse
from src.services.version import VersionService

router = APIRouter(prefix="/luu-tru")

@router.post(
    "/phien-ban/{file_id}",
    response_model=APIResponse[Any],
    status_code=201,
)
async def create_file_version(
    file_id: str,
    new_url: str = Body(..., embed=True),
    new_size: int = Body(..., embed=True),
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await VersionService.create_file_version(file_id, current_user.id, new_url, new_size)
    return APIResponse(data=result, message="Tạo phiên bản tệp mới hoàn tất", status=201)

@router.get("/phien-ban/{file_id}", response_model=APIResponse[Any])
async def get_file_versions(
    file_id: str,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await VersionService.get_file_versions(file_id, current_user.id)
    return APIResponse(data=result, message="Trích xuất lịch sử phiên bản tệp hoàn tất")

@router.post("/phien-ban/{file_id}/khoi-phuc/{version_id}", response_model=APIResponse[Any])
async def restore_file_version(
    file_id: str,
    version_id: str,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await VersionService.restore_file_version(file_id, version_id, current_user.id)
    return APIResponse(data=result, message="Khôi phục phiên bản tệp hoàn tất")
