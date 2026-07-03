from src.core.dependency import CurrentUser
from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from src.services.audit import AuditService

from src.core.dependency import get_current_user, get_db, require_role
from src.core.response import APIResponse
from src.core.dependency import Role

router = APIRouter(route_class=LoggingRoute, prefix="/kiem-toan")

@router.get(
    "/logs",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_activity(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await AuditService.get_moderator_activity_log(str(current_user.id)),
        message="Lấy nhật ký hoạt động thành công",
    )
