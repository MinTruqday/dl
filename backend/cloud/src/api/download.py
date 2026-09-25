from typing import Any

from fastapi import APIRouter, Depends, Query

from src.core.dependency import CurrentUser, get_current_user, get_db
from src.core.response import APIResponse
from src.services.download import DownloadService

router = APIRouter(prefix="/tai-ve")


@router.get("/{file_id}/duong-dan", response_model=APIResponse[Any])
async def get_download_url(
    file_id: str,
    expires_in: int = Query(3600, ge=60, le=86400),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    res = await DownloadService.generate_download_url(
        file_id, current_user.id, expires_in=expires_in
    )
    return APIResponse(data=res, message="Tạo đường dẫn tải về thành công")
