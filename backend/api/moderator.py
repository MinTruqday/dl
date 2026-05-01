from typing import Any, Optional
from fastapi import APIRouter, Depends
from api.dependencies import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.moderation import ModerationService
from services.document import DocumentService
from services.payout import PayoutService
from services.system_config import SystemConfigService
from services.comment import CommentService
from services.moderator import ModeratorService
from pydantic import BaseModel

router = APIRouter(prefix="/moderator")

class ModerationActionRequest(BaseModel):
    reason: str
    duration_hours: Optional[int] = 24

class TagRequest(BaseModel):
    name: str

class BlacklistRequest(BaseModel):
    keyword: str

class ModerateDocumentRequest(BaseModel):
    action: str
    reason: str

class NoteRequest(BaseModel):
    note: str

class ResolveReportRequest(BaseModel):
    action: str

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

@router.post("/users/{user_id}/warn", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def warn_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.warn_user(user_id, req.reason, current_user),
        message="Gửi cảnh báo thành công."
    )

@router.post("/users/{user_id}/lock", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def lock_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.lock_user(user_id, req.reason, req.duration_hours, current_user),
        message="Khóa tài khoản thành công."
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

@router.get("/payouts", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_payouts(status: str = "pending"):
    return APIResponse(
        data=await PayoutService.get_payout_queue(status),
        message="Lấy hàng đợi thanh toán thành công."
    )

@router.post("/payouts/{payout_id}/{action}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_payout(payout_id: str, action: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PayoutService.verify_payout(payout_id, action, current_user),
        message="Xử lý thanh toán thành công."
    )

@router.post("/tags", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def create_tag(req: TagRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SystemConfigService.manage_tags("create", req.name, current_user),
        message="Tạo thẻ thành công.",
        status=201
    )

@router.delete("/tags/{tag_name}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def delete_tag(tag_name: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SystemConfigService.manage_tags("delete", tag_name, current_user),
        message="Xóa thẻ thành công."
    )

@router.post("/blacklist", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def add_to_blacklist(req: BlacklistRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SystemConfigService.manage_blacklist("add", req.keyword, current_user),
        message="Thêm từ khóa cấm thành công.",
        status=201
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

@router.delete("/users/{user_id}/comments", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def bulk_delete_comments(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await CommentService.bulk_delete_comments(user_id, current_user),
        message="Xóa bình luận thành công."
    )

@router.get("/users/{user_id}/notes", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_moderator_notes(user_id: str):
    return APIResponse(
        data=await ModerationService.get_moderator_notes(user_id),
        message="Lấy ghi chú thành công."
    )

@router.post("/users/{user_id}/notes", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def add_moderator_note(user_id: str, req: NoteRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.add_moderator_note(user_id, req.note, current_user),
        message="Thêm ghi chú thành công.",
        status=201
    )

@router.get("/activity", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_activity(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ModerationService.get_moderator_activity_log(str(current_user.id)),
        message="Lấy nhật ký hoạt động thành công."
    )
