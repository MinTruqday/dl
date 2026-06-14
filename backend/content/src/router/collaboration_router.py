from typing import Any, List

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends
from src.router.dependency_router import get_db, require_role
from src.schemas.document_schema import (
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
from src.services.collaboration_service import CollaborationService

router = APIRouter(prefix="/collaboration")


@router.post("/invitations", response_model=APIResponse[Any])
async def invite_collaborator(
    data: CoauthorInviteRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.send_collaboration_invite(
            data.document_id, data.email, data.role, current_user, db=db
        ),
        message="The editorial collaboration invitation has been successfully dispatched to the designated user",
        status=201,
    )


@router.get("/invitations", response_model=APIResponse[Any])
async def get_my_collaboration_invites(
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_my_collaboration_invites(
            current_user, db=db
        ),
        message="The list of active editorial collaboration invitations has been successfully retrieved",
    )


@router.patch("/invitations/{invite_id}", response_model=APIResponse[Any])
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
        message="Your response to the editorial collaboration invitation has been successfully recorded",
    )


@router.get("/documents/{document_id}", response_model=APIResponse[Any])
async def get_collaborators(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_collaborators(
            document_id, current_user, db=db
        ),
        message="The list of actively assigned editorial collaborators has been successfully retrieved",
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
        message="The specified editorial collaborator has been successfully removed from the designated document",
    )


@router.get("/documents/{document_id}/activity", response_model=APIResponse[Any])
async def get_activities(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_activities(
            document_id, current_user, db=db
        ),
        message="The comprehensive editorial activity history for the specified document has been successfully retrieved",
    )


@router.post(
    "/documents/{document_id}/transfer-ownership", response_model=APIResponse[Any]
)
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
        message="The primary administrative ownership of the collaborative document has been successfully transferred",
    )


@router.post("/documents/{document_id}/ping", response_model=APIResponse[Any])
async def ping_status(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.update_status(document_id, current_user, db=db),
        message="Your active presence status within the collaborative editorial environment has been successfully synchronized",
    )


@router.get("/documents/{document_id}/online", response_model=APIResponse[Any])
async def get_online_collaborators(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_online_collaborators(document_id, db=db),
        message="The list of currently active online editorial collaborators has been successfully retrieved",
    )


@router.patch("/{collaboration_id}/roles", response_model=APIResponse[Any])
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
        message="The specific access and modification privileges for the designated collaborator have been successfully updated",
    )


@router.post("/documents/{document_id}/messages", response_model=APIResponse[Any])
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
        message="The internal collaborative communication message has been successfully transmitted to the editorial team",
    )


@router.get("/documents/{document_id}/messages", response_model=APIResponse[Any])
async def get_memos(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_memos(document_id, current_user, db=db),
        message="The internal collaborative communication history has been successfully retrieved from the system",
    )


@router.patch("/documents/{document_id}/access", response_model=APIResponse[Any])
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
        message="The global collaborative access permission configurations have been successfully updated",
    )


@router.get("/documents/{document_id}/sent-invitations", response_model=APIResponse[Any])
async def get_sent_pending_invites(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_sent_pending_invites(
            document_id, current_user, db=db
        ),
        message="The list of pending outgoing collaboration invitations has been successfully compiled and retrieved",
    )


@router.delete("/invitations/{invite_id}", response_model=APIResponse[Any])
async def revoke_invite(
    invite_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.revoke_invite(invite_id, current_user, db=db),
        message="The previously dispatched collaborative invitation has been successfully revoked and invalidated",
    )


@router.get(
    "/documents/{document_id}/contribution-stats", response_model=APIResponse[Any]
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
        message="The detailed collaborative contribution metrics and statistics have been successfully calculated and retrieved",
    )


@router.post("/documents/{document_id}/versions", response_model=APIResponse[Any])
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
        message="A new historical snapshot of the collaborative document has been successfully preserved",
        status=201,
    )


@router.get("/documents/{document_id}/versions", response_model=APIResponse[Any])
async def get_snapshots(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_snapshots(document_id, current_user, db=db),
        message="The chronological list of historical document snapshots has been successfully retrieved",
    )


@router.post("/documents/{document_id}/lock", response_model=APIResponse[Any])
async def acquire_lock(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.acquire_lock(document_id, current_user, db=db),
        message="The exclusive editorial modification lock has been successfully acquired for the current session",
    )


@router.post("/documents/{document_id}/unlock", response_model=APIResponse[Any])
async def release_lock(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.release_lock(document_id, current_user, db=db),
        message="The exclusive editorial modification lock has been successfully released and the session has ended",
    )


@router.get("/documents/{document_id}/lock-status", response_model=APIResponse[Any])
async def get_lock_status(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_lock_status(document_id, db=db),
        message="The current editorial modification lock status has been successfully verified",
    )


@router.post("/documents/{document_id}/invite-codes", response_model=APIResponse[Any])
async def generate_invite_code(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.generate_invite_code(
            document_id, current_user, db=db
        ),
        message="A secure access token for joining the collaborative environment has been successfully generated",
    )


@router.post("/join/{invite_code}", response_model=APIResponse[Any])
async def join_via_invite_code(
    invite_code: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.join_via_invite_code(
            invite_code, current_user, db=db
        ),
        message="You have successfully joined the collaborative editorial group using the provided access token",
    )


@router.post("/documents/{document_id}/tasks", response_model=APIResponse[Any])
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
        message="The new editorial collaborative task has been successfully created and assigned",
        status=201,
    )


@router.get("/documents/{document_id}/tasks", response_model=APIResponse[Any])
async def get_tasks(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_tasks(document_id, current_user, db=db),
        message="The list of active editorial collaborative tasks has been successfully retrieved",
    )


@router.patch("/tasks/{task_id}", response_model=APIResponse[Any])
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
        message="The operational status of the specified editorial collaborative task has been successfully updated",
    )


@router.post("/tasks/{task_id}/comments", response_model=APIResponse[Any])
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
        message="Your communicative comment has been successfully attached to the specified editorial task",
        status=201,
    )


@router.get("/tasks/{task_id}/comments", response_model=APIResponse[Any])
async def get_task_comments(
    task_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CollaborationService.get_task_comments(task_id, current_user, db=db),
        message="The communicative comments associated with the specified editorial task have been successfully retrieved",
    )