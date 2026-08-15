from typing import Any
from fastapi import APIRouter, Depends, Query
from src.core.response import APIResponse
from src.api.dependency import get_db, require_role
from src.core.dependency import CurrentUser, Role
from src.services.download import DownloadService

router = APIRouter(prefix="/tai-ve")

@router.get("/{file_id}/duong-dan", response_model=APIResponse[Any])
async def get_download_url(
    file_id: str,
    expires_in: int = Query(3600, ge=60, le=86400),
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    res = await DownloadService.generate_download_url(file_id, current_user.id, expires_in=expires_in)
    return APIResponse(data=res, message="Tạo đường dẫn tải về thành công")
