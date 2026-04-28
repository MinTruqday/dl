from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from api.dependencies import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from services.moderator import ModeratorService
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/moderator")

class ModerationActionRequest(BaseModel):
    reason: str
    duration_hours: Optional[int] = 24

class TagRequest(BaseModel):
    name: str

class BlacklistRequest(BaseModel):
    keyword: str

class ContentRemovalRequest(BaseModel):
    item_type: str
    item_id: str
    reason: str

@router.get("/reports", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_reports(status: str = "pending", skip: int = 0, limit: int = 30):
    return APIResponse(data=await ModeratorService.get_report_queue(status, skip, limit), message="Lấy danh sách báo cáo vi phạm thành công.", status=200)

@router.post("/users/{user_id}/warn", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def warn_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.warn_user(user_id, req.reason, current_user), message="Gửi cảnh báo cho người dùng thành công.", status=200)

@router.post("/users/{user_id}/lock", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def lock_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.lock_user(user_id, req.reason, req.duration_hours, current_user), message="Khóa tài khoản người dùng thành công.", status=200)

@router.post("/tags", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def create_tag(req: TagRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.manage_tags("create", req.name, current_user), message="Tạo thẻ phân loại mới thành công.", status=201)

@router.delete("/tags/{tag_name}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def delete_tag(tag_name: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.manage_tags("delete", tag_name, current_user), message="Xóa thẻ phân loại thành công.", status=200)

@router.get("/tags", response_model=APIResponse[Any])
async def get_tags():
    return APIResponse(data=await ModeratorService.get_all_tags(), message="Lấy danh sách tất cả thẻ phân loại thành công.", status=200)

@router.post("/blacklist", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def add_to_blacklist(req: BlacklistRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.manage_blacklist("add", req.keyword, current_user), message="Thêm từ khóa vào danh sách đen thành công.", status=201)

@router.delete("/blacklist/{keyword}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def delete_blacklist_keyword(keyword: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.manage_blacklist("remove", keyword, current_user), message="Xóa từ khóa khỏi danh sách đen thành công.", status=200)

@router.get("/blacklist", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_blacklist():
    return APIResponse(data=await ModeratorService.get_blacklist(), message="Lấy danh sách từ khóa bị chặn thành công.", status=200)

@router.post("/content/remove", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def remove_content(req: ContentRemovalRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.remove_violating_content(req.item_type, req.item_id, req.reason, current_user), message="Gỡ bỏ nội dung vi phạm thành công.", status=200)

@router.get("/metrics", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_metrics():
    return APIResponse(data=await ModeratorService.get_community_metrics(), message="Lấy số liệu thống kê cộng đồng thành công.", status=200)

@router.get("/activity", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_activity(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.get_moderator_activity_log(str(current_user.id)), message="Lấy nhật ký hoạt động điều hành thành công.", status=200)
@router.get("/payouts", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_payouts(status: str = "pending"):
    return APIResponse(data=await ModeratorService.get_payout_queue(status), message="Lấy danh sách yêu cầu thanh toán thành công.", status=200)

@router.post("/payouts/{payout_id}/{action}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_payout(payout_id: str, action: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.verify_payout(payout_id, action, current_user), message="Xác thực yêu cầu thanh toán thành công.", status=200)

@router.get("/approval-queue", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_approval_queue(skip: int = 0, limit: int = 30):
    return APIResponse(data=await ModeratorService.get_approval_queue(skip, limit), message="Lấy hàng đợi phê duyệt nội dung thành công.", status=200)

class ModerateDocumentRequest(BaseModel):
    action: str
    reason: str

@router.post("/documents/{document_id}/moderate", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def moderate_document(document_id: str, req: ModerateDocumentRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.moderate_document(document_id, req.action, req.reason, current_user), message="Điều hành nội dung tài liệu thành công.", status=200)

@router.post("/users/{user_id}/shadowban", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def shadowban_user(user_id: str, is_banned: bool, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.shadowban_user(user_id, is_banned, current_user), message="Cập nhật trạng thái chặn ngầm người dùng thành công.", status=200)

@router.post("/users/{user_id}/kyc/{status}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_kyc(user_id: str, status: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.verify_kyc(user_id, status, current_user), message="Xác thực danh tính (KYC) người dùng thành công.", status=200)

@router.delete("/users/{user_id}/comments", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def bulk_delete_comments(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.bulk_delete_comments(user_id, current_user), message="Xóa hàng loạt bình luận của người dùng thành công.", status=200)

@router.get("/users/{user_id}/notes", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_moderator_notes(user_id: str):
    return APIResponse(data=await ModeratorService.get_moderator_notes(user_id), message="Lấy danh sách ghi chú điều hành thành công.", status=200)

class NoteRequest(BaseModel):
    note: str

@router.post("/users/{user_id}/notes", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def add_moderator_note(user_id: str, req: NoteRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ModeratorService.add_moderator_note(user_id, req.note, current_user), message="Thêm ghi chú điều hành thành công.", status=201)
