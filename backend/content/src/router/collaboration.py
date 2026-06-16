from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from core.dependency import get_db, require_role
from src.schemas.documents import CoauthorInviteRequest, CollaborationResponse, CollabMemoCreateRequest, CollabTaskCreateRequest, CreateDraftSnapshotRequest, TaskCommentCreateRequest, TransferOwnershipRequest, UpdateCollabAccessRequest, UpdateCollaboratorRoleRequest, UpdateTaskStatusRequest
from src.services.collaboration import CollaborationService

router = APIRouter(prefix="/cong-tac")

@router.post("/loi-moi", response_model=APIResponse[Any])
async def invite_collaborator(data: CoauthorInviteRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.send_collaboration_invite(data.document_id, data.email, data.role, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.get("/loi-moi", response_model=APIResponse[Any])
async def get_my_collaboration_invites(current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_my_collaboration_invites(current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.patch("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def respond_to_collaboration_invite(invite_id: str, data: CollaborationResponse, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.respond_to_collaboration_invite(invite_id, data.status, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_collaborators(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_collaborators(document_id, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.delete("/{collaboration_id}", response_model=APIResponse[Any])
async def remove_collaborator(collaboration_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.remove_collaborator(collaboration_id, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
    )

@router.get("/tai-lieu/{document_id}/hoat-dong", response_model=APIResponse[Any])
async def get_activities(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_activities(document_id, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
    )

@router.post("/tai-lieu/{document_id}/chuyen-khoan-so-huu", response_model=APIResponse[Any])
async def transfer_ownership(document_id: str, data: TransferOwnershipRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.transfer_ownership(document_id, data.user_id, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
    )

@router.post("/tai-lieu/{document_id}/kiem-tra", response_model=APIResponse[Any])
async def ping_status(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.update_status(document_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.get("/tai-lieu/{document_id}/truc-tuyen", response_model=APIResponse[Any])
async def get_online_collaborators(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_online_collaborators(document_id, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.patch("/{collaboration_id}/vai-tro", response_model=APIResponse[Any])
async def update_collaborator_role(collaboration_id: str, data: UpdateCollaboratorRoleRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.update_collaborator_role(collaboration_id, data.role, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.post("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def send_memo(document_id: str, data: CollabMemoCreateRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.send_memo(document_id, data.message, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.get("/tai-lieu/{document_id}/tin-nhan", response_model=APIResponse[Any])
async def get_memos(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_memos(document_id, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
    )

@router.patch("/tai-lieu/{document_id}/truy-cap", response_model=APIResponse[Any])
async def update_collab_access(document_id: str, data: UpdateCollabAccessRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.update_collab_access(document_id, data.access_level, current_user, db=db),
        message="Mất kết nối mạng tạm thời",
    )

@router.get("/tai-lieu/{document_id}/da-gui-loi-moi", response_model=APIResponse[Any])
async def get_sent_pending_invites(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_sent_pending_invites(document_id, current_user, db=db),
        message="Mất kết nối mạng tạm thời",
    )

@router.delete("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def revoke_invite(invite_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.revoke_invite(invite_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.get("/tai-lieu/{document_id}/dong-gop-thong-ke", response_model=APIResponse[Any])
async def get_contribution_stats(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_contribution_stats(document_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.post("/tai-lieu/{document_id}/phien-lam-cam-quyen", response_model=APIResponse[Any])
async def create_snapshot(document_id: str, data: CreateDraftSnapshotRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.create_snapshot(document_id, data.version_name, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        status=201,
    )

@router.get("/tai-lieu/{document_id}/phien-lam-cam-quyen", response_model=APIResponse[Any])
async def get_snapshots(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_snapshots(document_id, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
    )

@router.post("/tai-lieu/{document_id}/khoa-lai", response_model=APIResponse[Any])
async def acquire_lock(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.acquire_lock(document_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.post("/tai-lieu/{document_id}/mo-khoa-lai", response_model=APIResponse[Any])
async def release_lock(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.release_lock(document_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.get("/tai-lieu/{document_id}/khoa-lai-trang-thai", response_model=APIResponse[Any])
async def get_lock_status(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_lock_status(document_id, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.post("/tai-lieu/{document_id}/loi-moi-ma-so", response_model=APIResponse[Any])
async def generate_invite_code(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.generate_invite_code(document_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.post("/tham-gia/{invite_code}", response_model=APIResponse[Any])
async def join_via_invite_code(invite_code: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.join_via_invite_code(invite_code, current_user, db=db),
        message="Lỗi xử lý tài khoản",
    )

@router.post("/tai-lieu/{document_id}/nhiem-vu", response_model=APIResponse[Any])
async def create_task(document_id: str, data: CollabTaskCreateRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.create_task(document_id, data.task_desc, data.assigned_to, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        status=201,
    )

@router.get("/tai-lieu/{document_id}/nhiem-vu", response_model=APIResponse[Any])
async def get_tasks(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_tasks(document_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.patch("/nhiem-vu/{task_id}", response_model=APIResponse[Any])
async def update_task(task_id: str, data: UpdateTaskStatusRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.update_task(task_id, data.is_done, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )

@router.post("/nhiem-vu/{task_id}/binh-luan", response_model=APIResponse[Any])
async def add_task_comment(task_id: str, data: TaskCommentCreateRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.add_task_comment(task_id, data.comment_text, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        status=201,
    )

@router.get("/nhiem-vu/{task_id}/binh-luan", response_model=APIResponse[Any])
async def get_task_comments(task_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_task_comments(task_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )