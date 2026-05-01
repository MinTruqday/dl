from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.moderation import ModerationService
from services.document import DocumentService
from pydantic import BaseModel

router = APIRouter(prefix="/moderation")

class ResolveReportRequest(BaseModel):
    action: str

class ModerateDocumentRequest(BaseModel):
    action: str
    reason: str

@router.get("/reports", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_reports(status: str = "pending", skip: int = 0, limit: int = 30):
    return APIResponse(
        data=await ModerationService.get_report_queue(status, skip, limit),
        message="Lấy danh sách báo cáo thành công."
    )

@router.post("/reports/{report_id}/resolve", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def resolve_report(report_id: str, req: ResolveReportRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.resolve_report(report_id, req.action, current_user), 
        message="Xử lý báo cáo thành công."
    )

@router.get("/approval-queue", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_approval_queue(skip: int = 0, limit: int = 30):
    return APIResponse(
        data=await DocumentService.get_approval_queue(skip, limit),
        message="Lấy hàng đợi phê duyệt thành công."
    )

@router.post("/documents/{document_id}/moderate", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def moderate_document(document_id: str, req: ModerateDocumentRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.moderate_document(document_id, req.action, req.reason, current_user),
        message="Xử lý tài liệu thành công."
    )

@router.post("/users/{user_id}/shadowban", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def shadowban_user(user_id: str, is_banned: bool, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.shadowban_user(user_id, is_banned, current_user),
        message="Cập nhật shadowban thành công."
    )

@router.post("/users/{user_id}/kyc/{status}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_kyc(user_id: str, status: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.verify_kyc(user_id, status, current_user),
        message="Xử lý KYC thành công."
    )

@router.get("/users/{user_id}/notes", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_moderator_notes(user_id: str):
    return APIResponse(
        data=await ModerationService.get_moderator_notes(user_id),
        message="Lấy ghi chú thành công."
    )

@router.post("/users/{user_id}/notes", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def add_moderator_note(user_id: str, note: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.add_moderator_note(user_id, note, current_user),
        message="Thêm ghi chú thành công.",
        status=201
    )

@router.post("/disputes/{dispute_id}/resolve", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def resolve_copyright_dispute(dispute_id: str, resolution: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.resolve_copyright_dispute(dispute_id, resolution, current_user),
        message="Giải quyết tranh chấp bản quyền thành công."
    )

@router.post("/bugs/handle", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def handle_bug_report(data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.handle_bug_report(data, current_user),
        message="Xử lý báo cáo lỗi thành công."
    )

@router.post("/tasks/assign", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def assign_task(data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.assign_task(data, current_user),
        message="Phân công nhiệm vụ thành công."
    )

@router.post("/policies/propose", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def submit_policy_proposal(data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.submit_policy_proposal(data, current_user),
        message="Gửi đề xuất chính sách thành công."
    )
