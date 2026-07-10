from typing import Any
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from src.core.dependency import get_current_user
from src.core.response import APIResponse
from src.services.copyright import CopyrightService
from pydantic import BaseModel

router = APIRouter(route_class=LoggingRoute, prefix="/ban-quyen", tags=["Bản quyền"])

class DRMSettingsUpdate(BaseModel):
    disable_copy: bool = False
    hide_from_search: bool = False

@router.put(
    "/{document_id}",
    response_model=APIResponse[Any],
)
async def update_drm_settings(
    document_id: str,
    req: DRMSettingsUpdate,
    current_user = Depends(get_current_user),
):
    result = await CopyrightService.update_drm_settings(
        document_id,
        req.disable_copy,
        req.hide_from_search,
        current_user,
    )
    return APIResponse(
        data=result, message="Cập nhật cấu hình bảo vệ bản quyền tài liệu hoàn tất"
    )

@router.post(
    "/{dispute_id}/giai-quyet",
    response_model=APIResponse[Any],
)
async def resolve_copyright_dispute(
    dispute_id: str,
    resolution: str,
    current_user = Depends(get_current_user),
):
    result = await CopyrightService.resolve_copyright_dispute(
        dispute_id, resolution, current_user
    )
    return APIResponse(
        data=result, message="Giải quyết tranh chấp bản quyền hoàn tất"
    )
