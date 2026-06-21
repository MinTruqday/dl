from typing import Any, List

from fastapi import APIRouter, Depends
from src.api.system_dependency import get_db, require_role
from src.schemas.document_metadata import (
    CoauthorInviteRequest,
    CollabMemoCreateRequest,
    CollaborationResponse,
    CollabTaskCreateRequest,
    CreateDraftSnapshotRequest,
    TaskCommentCreateRequest,
    TransferOwnershipRequest,
    UpdateCollabAccessRequest,
    UpdateCollaboratorRoleRequest,
    UpdateTaskStatusRequest,
)
from src.services.collaboration_sync import CollaborationSync

from core.response import APIResponse
from core.dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/cong-tac")


@router.post("/loi-moi", response_model=APIResponse[Any])
async def invite_collaborator(
    data: CoauthorInviteRequest,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.send_collaboration_invite(
            data.document_id, data.email, data.role, current_user, db=db
        ),
        message="Gửi lời mời cộng tác thành công",
        status=201,
    )


@router.get("/loi-moi", response_model=APIResponse[Any])
async def get_my_collaboration_invites(
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_my_collaboration_invites(
            current_user, db=db
        ),
        message="Lấy danh sách lời mời cộng tác thành công",
    )


@router.patch("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def respond_to_collaboration_invite(
    invite_id: str,
    data: CollaborationResponse,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.respond_to_collaboration_invite(
            invite_id, data.status, current_user, db=db
        ),
        message="Phản hồi lời mời cộng tác thành công",
    )


@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_collaborators(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_collaborators(
            document_id, current_user, db=db
        ),
        message="Lấy danh sách cộng tác viên đang hoạt động thành công",
    )


@router.delete("/{collaboration_id}", response_model=APIResponse[Any])
async def remove_collaborator(
    collaboration_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.remove_collaborator(
            collaboration_id, current_user, db=db
        ),
        message="Xóa cộng tác viên thành công",
    )


@router.get("/tai-lieu/{document_id}/hoat-dong", response_model=APIResponse[Any])
async def get_activities(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_activities(
            document_id, current_user, db=db
        ),
        message="Lấy lịch sử chỉnh sửa tài liệu thành công",
    )


@router.post(
    "/documents/{document_id}/transfer-ownership", response_model=APIResponse[Any]
)
async def transfer_ownership(
    document_id: str,
    data: TransferOwnershipRequest,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.transfer_ownership(
            document_id, data.user_id, current_user, db=db
        ),
        message="Chuyển quyền sở hữu tài liệu cộng tác thành công",
    )


@router.post("/tai-lieu/{document_id}/ping", response_model=APIResponse[Any])
async def ping_status(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.update_status(document_id, current_user, db=db),
        message="Đồng bộ trạng thái hoạt động thành công",
    )


@router.get("/tai-lieu/{document_id}/truc-tuyen", response_model=APIResponse[Any])
async def get_online_collaborators(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_online_collaborators(document_id, db=db),
        message="Lấy danh sách cộng tác viên đang trực tuyến thành công",
    )


@router.patch("/{collaboration_id}/vai-tro", response_model=APIResponse[Any])
async def update_collaborator_role(
    collaboration_id: str,
    data: UpdateCollaboratorRoleRequest,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.update_collaborator_role(
            collaboration_id, data.role, current_user, db=db
        ),
        message="Cập nhật quyền cộng tác viên thành công",
    )


@router.post("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def send_memo(
    document_id: str,
    data: CollabMemoCreateRequest,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.send_memo(
            document_id, data.message, current_user, db=db
        ),
        message="Gửi tin nhắn cộng tác thành công",
    )


@router.get("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def get_memos(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_memos(document_id, current_user, db=db),
        message="Lấy lịch sử giao tiếp cộng tác thành công",
    )


@router.patch("/tai-lieu/{document_id}/quyen-truy-cap", response_model=APIResponse[Any])
async def update_collab_access(
    document_id: str,
    data: UpdateCollabAccessRequest,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.update_collab_access(
            document_id, data.access_level, current_user, db=db
        ),
        message="Cập nhật cấu hình quyền cộng tác thành công",
    )


@router.get(
    "/documents/{document_id}/sent-invitations", response_model=APIResponse[Any]
)
async def get_sent_pending_invites(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_sent_pending_invites(
            document_id, current_user, db=db
        ),
        message="Lấy danh sách lời mời cộng tác thành công",
    )


@router.delete("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def revoke_invite(
    invite_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.revoke_invite(invite_id, current_user, db=db),
        message="Thu hồi lời mời cộng tác thành công",
    )


@router.get(
    "/documents/{document_id}/contribution-stats", response_model=APIResponse[Any]
)
async def get_contribution_stats(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_contribution_stats(
            document_id, current_user, db=db
        ),
        message="Lấy thống kê đóng góp cộng tác thành công",
    )


@router.post("/tai-lieu/{document_id}/phien-ban", response_model=APIResponse[Any])
async def create_snapshot(
    document_id: str,
    data: CreateDraftSnapshotRequest,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.create_snapshot(
            document_id, data.version_name, current_user, db=db
        ),
        message="Lưu lịch sử tài liệu thành công",
        status=201,
    )


@router.get("/tai-lieu/{document_id}/phien-ban", response_model=APIResponse[Any])
async def get_snapshots(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_snapshots(document_id, current_user, db=db),
        message="Lấy lịch sử tài liệu thành công",
    )


@router.post("/tai-lieu/{document_id}/khoa", response_model=APIResponse[Any])
async def acquire_lock(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.acquire_lock(document_id, current_user, db=db),
        message="Đã khóa phiên chỉnh sửa",
    )


@router.post("/tai-lieu/{document_id}/mo-khoa", response_model=APIResponse[Any])
async def release_lock(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.release_lock(document_id, current_user, db=db),
        message="Đã mở khóa phiên chỉnh sửa",
    )


@router.get("/tai-lieu/{document_id}/trang-thai-khoa", response_model=APIResponse[Any])
async def get_lock_status(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_lock_status(document_id, db=db),
        message="Xác minh trạng thái khóa chỉnh sửa thành công",
    )


@router.post("/tai-lieu/{document_id}/ma-moi", response_model=APIResponse[Any])
async def generate_invite_code(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.generate_invite_code(
            document_id, current_user, db=db
        ),
        message="Tạo mã truy cập cộng tác thành công",
    )


@router.post("/tham-gia/{invite_code}", response_model=APIResponse[Any])
async def join_via_invite_code(
    invite_code: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.join_via_invite_code(
            invite_code, current_user, db=db
        ),
        message="Tham gia nhóm cộng tác thành công",
    )


@router.post("/tai-lieu/{document_id}/cong-viec", response_model=APIResponse[Any])
async def create_task(
    document_id: str,
    data: CollabTaskCreateRequest,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.create_task(
            document_id, data.task_desc, data.assigned_to, current_user, db=db
        ),
        message="Tạo nhiệm vụ cộng tác thành công",
        status=201,
    )


@router.get("/tai-lieu/{document_id}/cong-viec", response_model=APIResponse[Any])
async def get_tasks(
    document_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_tasks(document_id, current_user, db=db),
        message="Lấy danh sách tác vụ cộng tác thành công",
    )


@router.patch("/nhiem-vu/{task_id}", response_model=APIResponse[Any])
async def update_task(
    task_id: str,
    data: UpdateTaskStatusRequest,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.update_task(
            task_id, data.is_done, current_user, db=db
        ),
        message="Cập nhật trạng thái nhiệm vụ cộng tác thành công",
    )


@router.post("/nhiem-vu/{task_id}/binh-luan", response_model=APIResponse[Any])
async def add_task_comment(
    task_id: str,
    data: TaskCommentCreateRequest,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.add_task_comment(
            task_id, data.comment_text, current_user, db=db
        ),
        message="Gửi bình luận cộng tác thành công",
        status=201,
    )


@router.get("/nhiem-vu/{task_id}/binh-luan", response_model=APIResponse[Any])
async def get_task_comments(
    task_id: str,
    current_user: CurrentUser = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationSync.get_task_comments(task_id, current_user, db=db),
        message="Lấy danh sách bình luận cộng tác thành công",
    )
