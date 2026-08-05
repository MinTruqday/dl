from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from src.api.dependency import get_db, require_role
from src.schemas.document import (
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
    CollaborationShareLinkConfig,
    CollaborationShareLinkJoin,
    CollaborationAccessRequestCreate,
    CollaborationAccessRequestReview,
    CollaborationModeUpdate,
    CollaborationScheduleUpdate,
)
from src.services.collaboration import CollaborationService

from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]
OWNER_ROLES = [Role.AUTHOR, Role.ADMIN]

@router.post("/loi-moi", response_model=APIResponse[Any], status_code=201)
async def invite_collaborator(
    data: CoauthorInviteRequest,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.send_collaboration_invite(
            data.document_id, data.email, data.role, current_user
        ),
        message="Gửi lời mời cộng tác hoàn tất",
        status=201,
    )

@router.get("/loi-moi", response_model=APIResponse[Any])
async def get_my_collaboration_invites(
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_my_collaboration_invites(
            current_user
        ),
        message="Trích xuất danh sách lời mời tham gia cộng tác hoàn tất",
    )

@router.patch("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def respond_to_collaboration_invite(
    invite_id: str,
    data: CollaborationResponse,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.respond_to_collaboration_invite(
            invite_id, data.status, current_user
        ),
        message="Xử lý phản hồi lời mời cộng tác hoàn tất",
    )

@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_collaborators(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_collaborators(
            document_id, current_user
        ),
        message="Trích xuất danh sách thành viên cộng tác hiện tại hoàn tất",
    )

@router.delete("/{collaboration_id}", response_model=APIResponse[Any])
async def remove_collaborator(
    collaboration_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.remove_collaborator(
            collaboration_id, current_user
        ),
        message="Thu hồi quyền truy cập và xóa thành viên cộng tác hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/hoat-dong", response_model=APIResponse[Any])
async def get_activities(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_activities(
            document_id, current_user
        ),
        message="Trích xuất nhật ký hoạt động chỉnh sửa tài liệu hoàn tất",
    )

@router.post(
    "/documents/{document_id}/transfer-ownership", response_model=APIResponse[Any]
)
async def transfer_ownership(
    document_id: str,
    data: TransferOwnershipRequest,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.transfer_ownership(
            document_id, data.user_id, current_user
        ),
        message="Chuyển quyền sở hữu tài liệu cộng tác hoàn tất",
    )

@router.post("/tai-lieu/{document_id}/ping", response_model=APIResponse[Any])
async def ping_status(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_status(document_id, current_user),
        message="Đồng bộ hóa trạng thái hoạt động trực tuyến hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/truc-tuyen", response_model=APIResponse[Any])
async def get_online_collaborators(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_online_collaborators(document_id),
        message="Trích xuất danh sách cộng tác viên đang trực tuyến hoàn tất",
    )

@router.patch("/{collaboration_id}/vai-tro", response_model=APIResponse[Any])
async def update_collaborator_role(
    collaboration_id: str,
    data: UpdateCollaboratorRoleRequest,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_collaborator_role(
            collaboration_id, data.role, current_user
        ),
        message="Cập nhật cấu hình phân quyền cộng tác viên hoàn tất",
    )

@router.post("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def send_memo(
    document_id: str,
    data: CollabMemoCreateRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.send_memo(
            document_id, data.message, current_user
        ),
        message="Phân phối tin nhắn cộng tác nội bộ hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def get_memos(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_memos(document_id, current_user),
        message="Trích xuất nhật ký tin nhắn cộng tác nội bộ hoàn tất",
    )

@router.patch("/tai-lieu/{document_id}/quyen-truy-cap", response_model=APIResponse[Any])
async def update_collab_access(
    document_id: str,
    data: UpdateCollabAccessRequest,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_collab_access(
            document_id, data.access_level, current_user
        ),
        message="Cập nhật cấu hình mức độ quyền truy cập cộng tác hoàn tất",
    )

@router.get(
    "/documents/{document_id}/sent-invitations", response_model=APIResponse[Any]
)
async def get_sent_pending_invites(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_sent_pending_invites(
            document_id, current_user
        ),
        message="Trích xuất danh sách lời mời tham gia cộng tác hoàn tất",
    )

@router.delete("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def revoke_invite(
    invite_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.revoke_invite(invite_id, current_user),
        message="Hủy bỏ và thu hồi lời mời tham gia cộng tác hoàn tất",
    )

@router.get(
    "/documents/{document_id}/contribution-stats", response_model=APIResponse[Any]
)
async def get_contribution_stats(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_contribution_stats(
            document_id, current_user
        ),
        message="Trích xuất báo cáo thống kê mức độ đóng góp hoàn tất",
    )

@router.post(
    "/tai-lieu/{document_id}/phien-ban",
    response_model=APIResponse[Any],
    status_code=201,
)
async def create_snapshot(
    document_id: str,
    data: CreateDraftSnapshotRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.create_snapshot(
            document_id, data.version_name, current_user
        ),
        message="Lưu trữ bản chụp phiên bản tài liệu hoàn tất",
        status=201,
    )

@router.get("/tai-lieu/{document_id}/phien-ban", response_model=APIResponse[Any])
async def get_snapshots(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_snapshots(document_id, current_user),
        message="Trích xuất danh sách bản chụp phiên bản tài liệu hoàn tất",
    )

@router.post("/tai-lieu/{document_id}/khoa", response_model=APIResponse[Any])
async def acquire_lock(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.acquire_lock(document_id, current_user),
        message="Thiết lập khóa phiên chỉnh sửa tài liệu hoàn tất",
    )

@router.post("/tai-lieu/{document_id}/mo-khoa", response_model=APIResponse[Any])
async def release_lock(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.release_lock(document_id, current_user),
        message="Hủy khóa phiên chỉnh sửa tài liệu hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/trang-thai-khoa", response_model=APIResponse[Any])
async def get_lock_status(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_lock_status(document_id),
        message="Kiểm tra trạng thái khóa phiên chỉnh sửa hiện tại hoàn tất",
    )

@router.post("/tai-lieu/{document_id}/ma-moi", response_model=APIResponse[Any])
async def generate_invite_code(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.generate_invite_code(
            document_id, current_user
        ),
        message="Khởi tạo mã mời tham gia cộng tác hoàn tất",
    )

@router.post("/tham-gia/{invite_code}", response_model=APIResponse[Any])
async def join_via_invite_code(
    invite_code: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.join_via_invite_code(
            invite_code, current_user
        ),
        message="Tham gia không gian cộng tác tài liệu hoàn tất",
    )

@router.post(
    "/tai-lieu/{document_id}/cong-viec",
    response_model=APIResponse[Any],
    status_code=201,
)
async def create_task(
    document_id: str,
    data: CollabTaskCreateRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.create_task(
            document_id, data.task_desc, data.assigned_to, current_user
        ),
        message="Khởi tạo nhiệm vụ cộng tác mới hoàn tất",
        status=201,
    )

@router.get("/tai-lieu/{document_id}/cong-viec", response_model=APIResponse[Any])
async def get_tasks(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_tasks(document_id, current_user),
        message="Trích xuất danh sách nhiệm vụ cộng tác hoàn tất",
    )

@router.patch("/nhiem-vu/{task_id}", response_model=APIResponse[Any])
async def update_task(
    task_id: str,
    data: UpdateTaskStatusRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_task(
            task_id, data.is_done, current_user
        ),
        message="Cập nhật trạng thái thực thi nhiệm vụ cộng tác hoàn tất",
    )

@router.post(
    "/nhiem-vu/{task_id}/binh-luan",
    response_model=APIResponse[Any],
    status_code=201,
)
async def add_task_comment(
    task_id: str,
    data: TaskCommentCreateRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.add_task_comment(
            task_id, data.comment_text, current_user
        ),
        message="Đăng tải bình luận thảo luận nhiệm vụ hoàn tất",
        status=201,
    )

@router.get("/nhiem-vu/{task_id}/binh-luan", response_model=APIResponse[Any])
async def get_task_comments(
    task_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_task_comments(task_id, current_user),
        message="Trích xuất danh sách bình luận thảo luận nhiệm vụ hoàn tất",
    )


@router.post("/tai-lieu/{document_id}/lien-ket-chia-se", response_model=APIResponse[Any])
async def configure_share_link(
    document_id: str,
    data: CollaborationShareLinkConfig,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.configure_share_link(
            document_id,
            data.is_active,
            data.password,
            data.default_role,
            data.expires_in_hours,
            current_user,
        ),
        message="Cấu hình liên kết chia sẻ cộng tác hoàn tất",
    )


@router.get("/tai-lieu/{document_id}/lien-ket-chia-se", response_model=APIResponse[Any])
async def get_share_link_config(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_share_link_config(document_id, current_user),
        message="Trích xuất thông tin cấu hình liên kết chia sẻ hoàn tất",
    )


@router.get("/thong-tin-lien-ket/{share_token}", response_model=APIResponse[Any])
async def get_public_share_link_info(
    share_token: str,
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_public_share_link_info(share_token),
        message="Trích xuất thông tin phòng cộng tác liên kết hoàn tất",
    )


@router.post("/tham-gia-lien-ket/{share_token}", response_model=APIResponse[Any])
async def join_via_share_link(
    share_token: str,
    data: CollaborationShareLinkJoin,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.join_via_share_link(
            share_token, data.password, current_user
        ),
        message="Xử lý gia nhập không gian cộng tác hoàn tất",
    )


@router.post("/tai-lieu/{document_id}/xin-quyen", response_model=APIResponse[Any], status_code=201)
async def create_access_request(
    document_id: str,
    data: CollaborationAccessRequestCreate,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.create_access_request(
            document_id, data.requested_role, data.message, current_user
        ),
        message="Gửi yêu cầu xin tham gia cộng tác hoàn tất",
        status=201,
    )


@router.get("/tai-lieu/{document_id}/yeu-cau-xin-quyen", response_model=APIResponse[Any])
async def get_document_access_requests(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_document_access_requests(
            document_id, current_user
        ),
        message="Trích xuất danh sách yêu cầu xin quyền hoàn tất",
    )


@router.get("/yeu-cau-xin-quyen-cua-toi", response_model=APIResponse[Any])
async def get_my_incoming_access_requests(
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_my_incoming_access_requests(current_user),
        message="Trích xuất danh sách yêu cầu xin quyền gửi tới tài liệu của bạn hoàn tất",
    )


@router.patch("/yeu-cau-xin-quyen/{request_id}", response_model=APIResponse[Any])
async def review_access_request(
    request_id: str,
    data: CollaborationAccessRequestReview,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.review_access_request(
            request_id, data.status, data.role, current_user
        ),
        message="Xử lý phản hồi yêu cầu xin quyền hoàn tất",
    )


@router.post("/tai-lieu/{document_id}/che-do-truy-cap", response_model=APIResponse[Any])
async def update_collaboration_mode(
    document_id: str,
    data: CollaborationModeUpdate,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_collaboration_mode(
            document_id, data.collaboration_mode, current_user
        ),
        message="Cập nhật chế độ đóng mở tài liệu hoàn tất",
    )


@router.get("/tai-lieu/{document_id}/che-do-truy-cap", response_model=APIResponse[Any])
async def get_collaboration_mode(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_collaboration_mode(document_id, current_user),
        message="Trích xuất thông tin chế độ đóng mở tài liệu hoàn tất",
    )


@router.post("/tai-lieu/{document_id}/lich-hen-gio", response_model=APIResponse[Any])
async def update_collaboration_schedules(
    document_id: str,
    data: CollaborationScheduleUpdate,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_collaboration_schedules(
            document_id, [s.model_dump() for s in data.schedules], current_user
        ),
        message="Cập nhật lịch hẹn giờ quyền hạn cộng tác hoàn tất",
    )


@router.get("/tai-lieu/{document_id}/lich-hen-gio", response_model=APIResponse[Any])
async def get_collaboration_schedules(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_collaboration_schedules(document_id, current_user),
        message="Trích xuất danh sách lịch hẹn giờ cộng tác hoàn tất",
    )


