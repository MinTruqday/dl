from typing import Any, Literal
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from src.core.dependency import Role, get_current_user, require_role
from src.core.response import APIResponse
from src.services.copyright import CopyrightService
from pydantic import BaseModel, Field

router = APIRouter(route_class=LoggingRoute, prefix="/ban-quyen")


class DRMSettingsUpdate(BaseModel):
    disable_copy: bool = False
    disable_print: bool = False
    hide_from_search: bool = False
    watermark_enabled: bool = True
    allow_internal_ai: bool = True
    license_valid_days: int = Field(default=30, ge=1, le=365)
    max_open_count: int = Field(default=100, ge=1, le=10000)
    ghost_font_enabled: bool = True
    ghost_font_exemption_scope: Literal[
        "owner_only", "private_link", "selected_users", "everyone"
    ] = "owner_only"
    ghost_font_exempt_user_ids: list[str] = Field(default_factory=list, max_length=100)


@router.put("/{document_id}", response_model=APIResponse[Any])
async def update_drm_settings(
    document_id: str, req: DRMSettingsUpdate, current_user=Depends(get_current_user)
):
    result = await CopyrightService.update_drm_settings(document_id, req.model_dump(), current_user)
    return APIResponse(data=result, message="Cập nhật cấu hình bảo vệ bản quyền tài liệu hoàn tất")


@router.post("/{dispute_id}/giai-quyet", response_model=APIResponse[Any])
async def resolve_copyright_dispute(
    dispute_id: str, resolution: str, current_user=Depends(require_role([Role.ADMIN]))
):
    result = await CopyrightService.resolve_copyright_dispute(dispute_id, resolution, current_user)
    return APIResponse(data=result, message="Giải quyết tranh chấp bản quyền hoàn tất")
