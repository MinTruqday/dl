from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.moderation import ModerationService
from pydantic import BaseModel

router = APIRouter(prefix="/reports")

class ResolveReportRequest(BaseModel):
    action: str

@router.get("/queue", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_reports(status: str = "pending", skip: int = 0, limit: int = 30):
    return APIResponse(
        data=await ModerationService.get_report_queue(status, skip, limit),
        message="Lấy danh sách báo cáo thành công."
    )

@router.post("/{report_id}/resolve", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def resolve_report(report_id: str, req: ResolveReportRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.resolve_report(report_id, req.action, current_user), 
        message="Xử lý báo cáo thành công."
    )
