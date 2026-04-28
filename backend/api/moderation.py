from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from models.user import UserInDB, RoleEnum
from api.dependencies import get_current_user, require_role
from services.moderation import ModerationService

router = APIRouter()

class ReportRequest(BaseModel):
    item_type: str 
    item_id: str
    reason: str
    description: Optional[str] = None

class ResolveReportRequest(BaseModel):
    action: str 

@router.post("/moderation/report", response_model=APIResponse[Any])
async def report_content(req: ReportRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModerationService.report_content(req, current_user), message="Gửi báo cáo nội dung thành công.", status=200)

@router.get("/admin/reports", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_pending_reports():
    return APIResponse(data=await ModerationService.get_pending_reports(), message="Lấy danh sách báo cáo đang chờ xử lý thành công.", status=200)

@router.post("/admin/reports/{report_id}/resolve", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def resolve_report(report_id: str, action: ResolveReportRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModerationService.resolve_report(report_id, action, current_user), message="Xử lý báo cáo thành công.", status=200)
