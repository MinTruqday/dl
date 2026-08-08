from typing import Any
from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.api.dependency import get_db, require_role
from src.services.activity import ActivityService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]

@router.get("/tai-lieu/{document_id}/hoat-dong", response_model=APIResponse[Any])
async def get_activities(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ActivityService.get_activities(document_id, current_user),
        message="Trích xuất nhật ký hoạt động chỉnh sửa tài liệu hoàn tất",
    )

@router.get("/documents/{document_id}/contribution-stats", response_model=APIResponse[Any])
async def get_contribution_stats(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ActivityService.get_contribution_stats(document_id, current_user),
        message="Trích xuất báo cáo thống kê mức độ đóng góp hoàn tất",
    )
