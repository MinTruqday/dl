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

@router.post("/moderation/report")
async def report_content(req: ReportRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ModerationService.report_content(req, current_user)

@router.get("/admin/reports", dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_pending_reports():
    return await ModerationService.get_pending_reports()

@router.post("/admin/reports/{report_id}/resolve", dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def resolve_report(report_id: str, action: ResolveReportRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ModerationService.resolve_report(report_id, action, current_user)
