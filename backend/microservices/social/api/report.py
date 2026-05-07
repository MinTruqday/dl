from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import require_role, get_current_user
from shared.models.user import UserInDB, RoleEnum
from shared.core.response import APIResponse
from services.user import UserService
from pydantic import BaseModel
router = APIRouter(prefix="/bao-cao")
class ResolveReportRequest(BaseModel):
    action: str
@router.get("/hang-doi", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_reports(status: str = "pending", skip: int = 0, limit: int = 30):
    return APIResponse(
        data=await UserService.get_report_queue(status, skip, limit),
        message="Lấy danh sách báo cáo thành công"
    )
@router.post("/{report_id}/giai-quyet", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def resolve_report(report_id: str, req: ResolveReportRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await UserService.resolve_report(report_id, req.action, current_user), 
        message="Xử lý báo cáo thành công"
    )
