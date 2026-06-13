from typing import Any, List

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends
from src.api.dependency import get_db, require_role
from src.schemas.document import (CoauthorInviteRequest,
                                  CollabMemoCreateRequest,
                                  CollaborationResponse,
                                  CollabTaskCreateRequest,
                                  CreateDraftSnapshotRequest,
                                  TaskCommentCreateRequest,
                                  TransferOwnershipRequest,
                                  UpdateCollabAccessRequest,
                                  UpdateCollaboratorRoleRequest,
                                  UpdateTaskStatusRequest)
from src.services.collaboration import CollaborationService

router = APIRouter(prefix="/cong-tac")


@router.post("/loi-moi", response_model=APIResponse[Any])
async def invite_collaborator(
    data: CoauthorInviteRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.send_collaboration_invite(
            data.document_id, data.email, data.role, current_user, db=db
        ),
        message="Đã gửi lời mời cộng tác",
        status=201,
    )


@router.get("/loi-moi", response_model=APIResponse[Any])
async def get_my_collaboration_invites(
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_my_collaboration_invites(
            current_user, db=db
        ),
        message="Đã tải danh sách lời mời",
    )


@router.patch("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def respond_to_collaboration_invite(
    invite_id: str,
    data: CollaborationResponse,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.respond_to_collaboration_invite(
            invite_id, data.status, current_user, db=db
        ),
        message="Đã phản hồi lời mời cộng tác",
    )


@router.get("/document/{document_id}", response_model=APIResponse[Any])
async def get_collaborators(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_collaborators(
            document_id, current_user, db=db
        ),
        message="Đã tải danh sách người cộng tác",
    )


@router.delete("/{collaboration_id}", response_model=APIResponse[Any])
async def remove_collaborator(
    collaboration_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.remove_collaborator(
            collaboration_id, current_user, db=db
        ),
        message="Đã xóa cộng tác viên",
    )


@router.get("/document/{document_id}/hoat-dong", response_model=APIResponse[Any])
async def get_activities(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_activities(
            document_id, current_user, db=db
        ),
        message="Đã tải danh sách lịch sử hoạt động",
    )


@router.post("/document/{document_id}/chuyen-quyen", response_model=APIResponse[Any])
async def transfer_ownership(
    document_id: str,
    data: TransferOwnershipRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.transfer_ownership(
            document_id, data.user_id, current_user, db=db
        ),
        message="Đã chuyển quyền sở hữu",
    )


@router.post("/document/{document_id}/ping", response_model=APIResponse[Any])
async def ping_status(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_status(document_id, current_user, db=db),
        message="Đã cập nhật trạng thái",
    )


@router.get("/document/{document_id}/truc-tuyen", response_model=APIResponse[Any])
async def get_online_collaborators(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_online_collaborators(document_id, db=db),
        message="Đã tải danh sách cộng tác viên trực tuyến",
    )


@router.patch("/{collaboration_id}/vai-tro", response_model=APIResponse[Any])
async def update_collaborator_role(
    collaboration_id: str,
    data: UpdateCollaboratorRoleRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_collaborator_role(
            collaboration_id, data.role, current_user, db=db
        ),
        message="Đã cập nhật vai trò cộng tác viên",
    )


@router.post("/document/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def send_memo(
    document_id: str,
    data: CollabMemoCreateRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.send_memo(
            document_id, data.message, current_user, db=db
        ),
        message="Đã gửi tin nhắn",
    )


@router.get("/document/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def get_memos(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_memos(document_id, current_user, db=db),
        message="Đã tải danh sách tin nhắn",
    )


@router.patch("/document/{document_id}/quyen-truy-cap", response_model=APIResponse[Any])
async def update_collab_access(
    document_id: str,
    data: UpdateCollabAccessRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_collab_access(
            document_id, data.access_level, current_user, db=db
        ),
        message="Đã cập nhật quyền truy cập mặc định",
    )


@router.get("/document/{document_id}/loi-moi-da-gui", response_model=APIResponse[Any])
async def get_sent_pending_invites(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_sent_pending_invites(
            document_id, current_user, db=db
        ),
        message="Đã tải danh sách lời mời đã gửi",
    )


@router.delete("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def revoke_invite(
    invite_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.revoke_invite(invite_id, current_user, db=db),
        message="Đã thu hồi lời mời",
    )


@router.get(
    "/document/{document_id}/contribution-stats", response_model=APIResponse[Any]
)
async def get_contribution_stats(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_contribution_stats(
            document_id, current_user, db=db
        ),
        message="Đã tải dữ liệu thống kê đóng góp",
    )


@router.post("/document/{document_id}/phien-ban", response_model=APIResponse[Any])
async def create_snapshot(
    document_id: str,
    data: CreateDraftSnapshotRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.create_snapshot(
            document_id, data.version_name, current_user, db=db
        ),
        message="Đã tạo phiên bản nháp cộng tác",
        status=201,
    )


@router.get("/document/{document_id}/phien-ban", response_model=APIResponse[Any])
async def get_snapshots(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_snapshots(document_id, current_user, db=db),
        message="Đã tải danh sách phiên bản nháp",
    )


@router.post("/document/{document_id}/khoa", response_model=APIResponse[Any])
async def acquire_lock(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.acquire_lock(document_id, current_user, db=db),
        message="Đã khóa độc quyền tài liệu",
    )


@router.post("/document/{document_id}/mo-khoa", response_model=APIResponse[Any])
async def release_lock(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.release_lock(document_id, current_user, db=db),
        message="Đã kết thúc biên tập và mở khóa tài liệu",
    )


@router.get("/document/{document_id}/status-khoa", response_model=APIResponse[Any])
async def get_lock_status(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_lock_status(document_id, db=db),
        message="Đã kiểm tra trạng thái khóa biên tập",
    )


@router.post("/document/{document_id}/ma-moi", response_model=APIResponse[Any])
async def generate_invite_code(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.generate_invite_code(
            document_id, current_user, db=db
        ),
        message="Đã tạo mã mời cộng tác",
    )


@router.post("/tham-gia/{invite_code}", response_model=APIResponse[Any])
async def join_via_invite_code(
    invite_code: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.join_via_invite_code(
            invite_code, current_user, db=db
        ),
        message="Đã tham gia nhóm cộng tác biên tập",
    )


@router.post("/document/{document_id}/nhiem-vu", response_model=APIResponse[Any])
async def create_task(
    document_id: str,
    data: CollabTaskCreateRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.create_task(
            document_id, data.task_desc, data.assigned_to, current_user, db=db
        ),
        message="Đã tạo nhiệm vụ cộng tác",
        status=201,
    )


@router.get("/document/{document_id}/nhiem-vu", response_model=APIResponse[Any])
async def get_tasks(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_tasks(document_id, current_user, db=db),
        message="Đã tải danh sách nhiệm vụ",
    )


@router.patch("/nhiem-vu/{task_id}", response_model=APIResponse[Any])
async def update_task(
    task_id: str,
    data: UpdateTaskStatusRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_task(
            task_id, data.is_done, current_user, db=db
        ),
        message="Đã cập nhật trạng thái nhiệm vụ",
    )


@router.post("/nhiem-vu/{task_id}/comment", response_model=APIResponse[Any])
async def add_task_comment(
    task_id: str,
    data: TaskCommentCreateRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.add_task_comment(
            task_id, data.comment_text, current_user, db=db
        ),
        message="Đã gửi bình luận nhiệm vụ",
        status=201,
    )


@router.get("/nhiem-vu/{task_id}/comment", response_model=APIResponse[Any])
async def get_task_comments(
    task_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_task_comments(task_id, current_user, db=db),
        message="Đã tải danh sách bình luận nhiệm vụ",
    )
