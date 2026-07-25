from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import require_role
from src.core.dependency import CurrentUser, Role
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.services.analytics import AnalyticsService

router = APIRouter(route_class=LoggingRoute, prefix="/luu-tru")

@router.get("/dung-luong/phan-tich", response_model=APIResponse[Any])
async def analyze_storage_quota(
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await AnalyticsService.analyze_storage_quota(current_user.id)
    return APIResponse(data=result, message="Phân tích hạn mức bộ nhớ hoàn tất")
