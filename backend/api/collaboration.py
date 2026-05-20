from typing import Any, List
from fastapi import APIRouter, Depends
from api.dependency import require_role
from models.user import UserInDB, RoleEnum
from models.document import (
    CoauthorInviteRequest,
    CollaborationResponse,
    TransferOwnershipRequest,
    UpdateCollaboratorRoleRequest,
    CollabMemoCreateRequest,
    UpdateCollabAccessRequest,
    CreateDraftSnapshotRequest,
    CollabTaskCreateRequest,
    UpdateTaskStatusRequest,
    TaskCommentCreateRequest,
)
from core.response import APIResponse
from services.collaboration import CollaborationService

router = APIRouter(prefix="/cong-tac")

@router.post("/loi-moi", response_model=APIResponse[Any])
async def invite_collaborator(data: CoauthorInviteRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.send_collaboration_invite(data.document_id, data.email, data.role, current_user),
        message="Gửi lời mời cộng tác thành công.",
        status=201
    )

@router.get("/loi-moi", response_model=APIResponse[Any])
async def get_my_collaboration_invites(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_my_collaboration_invites(current_user),
        message="Lấy danh sách lời mời thành công."
    )

@router.patch("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def respond_to_collaboration_invite(invite_id: str, data: CollaborationResponse, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.respond_to_collaboration_invite(invite_id, data.status, current_user),
        message="Đã phản hồi lời mời cộng tác."
    )

@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_collaborators(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_collaborators(document_id, current_user),
        message="Lấy danh sách người cộng tác thành công."
    )

@router.delete("/{collaboration_id}", response_model=APIResponse[Any])
async def remove_collaborator(collaboration_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.remove_collaborator(collaboration_id, current_user),
        message="Xóa cộng tác viên thành công."
    )

@router.get("/tai-lieu/{document_id}/hoat-dong", response_model=APIResponse[Any])
async def get_activities(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_activities(document_id, current_user),
        message="Lấy danh sách lịch sử hoạt động thành công."
    )

@router.post("/tai-lieu/{document_id}/chuyen-quyen", response_model=APIResponse[Any])
async def transfer_ownership(document_id: str, data: TransferOwnershipRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.transfer_ownership(document_id, data.user_id, current_user),
        message="Chuyển quyền sở hữu thành công."
    )

@router.post("/tai-lieu/{document_id}/ping", response_model=APIResponse[Any])
async def ping_status(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.update_status(document_id, current_user),
        message="Cập nhật trạng thái thành công."
    )

@router.get("/tai-lieu/{document_id}/truc-tuyen", response_model=APIResponse[Any])
async def get_online_collaborators(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_online_collaborators(document_id),
        message="Lấy danh sách cộng tác viên trực tuyến thành công."
    )

@router.patch("/{collaboration_id}/vai-tro", response_model=APIResponse[Any])
async def update_collaborator_role(collaboration_id: str, data: UpdateCollaboratorRoleRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.update_collaborator_role(collaboration_id, data.role, current_user),
        message="Thay đổi vai trò cộng tác viên thành công."
    )

@router.post("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def send_memo(document_id: str, data: CollabMemoCreateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.send_memo(document_id, data.message, current_user),
        message="Gửi tin nhắn thành công."
    )

@router.get("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def get_memos(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_memos(document_id, current_user),
        message="Lấy danh sách tin nhắn thành công."
    )

@router.patch("/tai-lieu/{document_id}/quyen-truy-cap", response_model=APIResponse[Any])
async def update_collab_access(document_id: str, data: UpdateCollabAccessRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.update_collab_access(document_id, data.access_level, current_user),
        message="Cập nhật quyền truy cập mặc định thành công."
    )

@router.get("/tai-lieu/{document_id}/loi-moi-da-gui", response_model=APIResponse[Any])
async def get_sent_pending_invites(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_sent_pending_invites(document_id, current_user),
        message="Lấy danh sách lời mời đã gửi thành công."
    )

@router.delete("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def revoke_invite(invite_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.revoke_invite(invite_id, current_user),
        message="Đã thu hồi lời mời thành công."
    )

@router.get("/tai-lieu/{document_id}/thong-ke-dong-gop", response_model=APIResponse[Any])
async def get_contribution_stats(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_contribution_stats(document_id, current_user),
        message="Lấy dữ liệu thống kê đóng góp thành công."
    )

@router.post("/tai-lieu/{document_id}/phien-ban", response_model=APIResponse[Any])
async def create_snapshot(document_id: str, data: CreateDraftSnapshotRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.create_snapshot(document_id, data.version_name, current_user),
        message="Đã tạo phiên bản nháp cộng tác thành công.",
        status=201
    )

@router.get("/tai-lieu/{document_id}/phien-ban", response_model=APIResponse[Any])
async def get_snapshots(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_snapshots(document_id, current_user),
        message="Lấy danh sách phiên bản nháp thành công."
    )

@router.post("/tai-lieu/{document_id}/khoa", response_model=APIResponse[Any])
async def acquire_lock(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.acquire_lock(document_id, current_user),
        message="Khóa độc quyền tài liệu thành công."
    )

@router.post("/tai-lieu/{document_id}/mo-khoa", response_model=APIResponse[Any])
async def release_lock(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.release_lock(document_id, current_user),
        message="Nhả khóa tài liệu thành công."
    )

@router.get("/tai-lieu/{document_id}/trang-thai-khoa", response_model=APIResponse[Any])
async def get_lock_status(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_lock_status(document_id),
        message="Lấy trạng thái khóa biên tập thành công."
    )

@router.post("/tai-lieu/{document_id}/ma-moi", response_model=APIResponse[Any])
async def generate_invite_code(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.generate_invite_code(document_id, current_user),
        message="Tạo mã mời cộng tác thành công."
    )

@router.post("/tham-gia/{invite_code}", response_model=APIResponse[Any])
async def join_via_invite_code(invite_code: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.join_via_invite_code(invite_code, current_user),
        message="Tham gia nhóm cộng tác biên tập thành công."
    )

@router.post("/tai-lieu/{document_id}/nhiem-vu", response_model=APIResponse[Any])
async def create_task(document_id: str, data: CollabTaskCreateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.create_task(document_id, data.task_desc, data.assigned_to, current_user),
        message="Tạo nhiệm vụ cộng tác thành công.",
        status=201
    )

@router.get("/tai-lieu/{document_id}/nhiem-vu", response_model=APIResponse[Any])
async def get_tasks(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_tasks(document_id, current_user),
        message="Lấy danh sách nhiệm vụ thành công."
    )

@router.patch("/nhiem-vu/{task_id}", response_model=APIResponse[Any])
async def update_task(task_id: str, data: UpdateTaskStatusRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.update_task(task_id, data.is_done, current_user),
        message="Cập nhật trạng thái nhiệm vụ thành công."
    )

@router.post("/nhiem-vu/{task_id}/binh-luan", response_model=APIResponse[Any])
async def add_task_comment(task_id: str, data: TaskCommentCreateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.add_task_comment(task_id, data.comment_text, current_user),
        message="Gửi bình luận nhiệm vụ thành công.",
        status=201
    )

@router.get("/nhiem-vu/{task_id}/binh-luan", response_model=APIResponse[Any])
async def get_task_comments(task_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_task_comments(task_id, current_user),
        message="Lấy danh sách bình luận nhiệm vụ thành công."
    )
