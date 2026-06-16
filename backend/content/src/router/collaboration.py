from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from core.dependency import get_db, require_role
from src.schemas.documents import CoauthorInviteRequest, CollaborationResponse, CollabMemoCreateRequest, CollabTaskCreateRequest, CreateDraftSnapshotRequest, TaskCommentCreateRequest, TransferOwnershipRequest, UpdateCollabAccessRequest, UpdateCollaboratorRoleRequest, UpdateTaskStatusRequest
from src.services.collaboration import CollaborationService

router = APIRouter(prefix="/collaboration")

@router.post("/invitations", response_model=APIResponse[Any])
async def invite_collaborator(data: CoauthorInviteRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.send_collaboration_invite(data.document_id, data.email, data.role, current_user, db=db),
        message="Editorial collaboration invitation token successfully dispatched notifying designated external user profile",
        status=201,
    )

@router.get("/invitations", response_model=APIResponse[Any])
async def get_my_collaboration_invites(current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_my_collaboration_invites(current_user, db=db),
        message="Active pending editorial collaboration invitations queue effectively fetched returning valid lists",
    )

@router.patch("/invitations/{invite_id}", response_model=APIResponse[Any])
async def respond_to_collaboration_invite(invite_id: str, data: CollaborationResponse, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.respond_to_collaboration_invite(invite_id, data.status, current_user, db=db),
        message="System securely processed definitive response handling pending active collaboration invitation logic",
    )

@router.get("/documents/{document_id}", response_model=APIResponse[Any])
async def get_collaborators(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_collaborators(document_id, current_user, db=db),
        message="Actively participating editorial collaborative members associated with specified document successfully retrieved",
    )

@router.delete("/{collaboration_id}", response_model=APIResponse[Any])
async def remove_collaborator(collaboration_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.remove_collaborator(collaboration_id, current_user, db=db),
        message="Specified editorial collaborator proactively removed detaching access viewing targeted document framework",
    )

@router.get("/documents/{document_id}/activity", response_model=APIResponse[Any])
async def get_activities(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_activities(document_id, current_user, db=db),
        message="Comprehensive systemic editorial chronological activity records tracking specified document thoroughly retrieved",
    )

@router.post("/documents/{document_id}/transfer-ownership", response_model=APIResponse[Any])
async def transfer_ownership(document_id: str, data: TransferOwnershipRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.transfer_ownership(document_id, data.user_id, current_user, db=db),
        message="Fundamental administrative governance migrating collaborative document safely shifted designating alternative owner",
    )

@router.post("/documents/{document_id}/ping", response_model=APIResponse[Any])
async def ping_status(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.update_status(document_id, current_user, db=db),
        message="Session active heartbeat presence status inside unified editorial workspace synchronized functionally",
    )

@router.get("/documents/{document_id}/online", response_model=APIResponse[Any])
async def get_online_collaborators(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_online_collaborators(document_id, db=db),
        message="Array tracking currently operating active online editorial workspace participants securely resolved",
    )

@router.patch("/{collaboration_id}/roles", response_model=APIResponse[Any])
async def update_collaborator_role(collaboration_id: str, data: UpdateCollaboratorRoleRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.update_collaborator_role(collaboration_id, data.role, current_user, db=db),
        message="Authorized functional access modification capability assigned explicitly designated collaborator effectively updated",
    )

@router.post("/documents/{document_id}/messages", response_model=APIResponse[Any])
async def send_memo(document_id: str, data: CollabMemoCreateRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.send_memo(document_id, data.message, current_user, db=db),
        message="Internal workspace messaging payload dispatched actively communicating participating editorial personnel reliably",
    )

@router.get("/documents/{document_id}/messages", response_model=APIResponse[Any])
async def get_memos(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_memos(document_id, current_user, db=db),
        message="Historical internal collaborative textual communication logs collected traversing organizational architectural framework",
    )

@router.patch("/documents/{document_id}/access", response_model=APIResponse[Any])
async def update_collab_access(document_id: str, data: UpdateCollabAccessRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.update_collab_access(document_id, data.access_level, current_user, db=db),
        message="Underlying global collaborative network structural boundary conditions functionally modified preventing incidents",
    )

@router.get("/documents/{document_id}/sent-invitations", response_model=APIResponse[Any])
async def get_sent_pending_invites(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_sent_pending_invites(document_id, current_user, db=db),
        message="List summarizing pending active outgoing group network participation invitations retrieved effectively",
    )

@router.delete("/invitations/{invite_id}", response_model=APIResponse[Any])
async def revoke_invite(invite_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.revoke_invite(invite_id, current_user, db=db),
        message="Formerly distributed participation access token conclusively revoked blocking unwanted systematic infiltration",
    )

@router.get("/documents/{document_id}/contribution-stats", response_model=APIResponse[Any])
async def get_contribution_stats(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_contribution_stats(document_id, current_user, db=db),
        message="Calculated metrics summarizing specific collaborative operational engagement milestones properly processed retrieving",
    )

@router.post("/documents/{document_id}/versions", response_model=APIResponse[Any])
async def create_snapshot(document_id: str, data: CreateDraftSnapshotRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.create_snapshot(document_id, data.version_name, current_user, db=db),
        message="Permanent systemic structural progression snapshot accurately captured freezing digital collaborative history",
        status=201,
    )

@router.get("/documents/{document_id}/versions", response_model=APIResponse[Any])
async def get_snapshots(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_snapshots(document_id, current_user, db=db),
        message="Chronological sequence encapsulating historical document backup snapshots logically retrieved restoring visibility",
    )

@router.post("/documents/{document_id}/lock", response_model=APIResponse[Any])
async def acquire_lock(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.acquire_lock(document_id, current_user, db=db),
        message="Exclusive administrative editing modification lock physically established reserving active local session",
    )

@router.post("/documents/{document_id}/unlock", response_model=APIResponse[Any])
async def release_lock(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.release_lock(document_id, current_user, db=db),
        message="Targeted overriding editorial structural manipulation lock conclusively relinquished detaching local session",
    )

@router.get("/documents/{document_id}/lock-status", response_model=APIResponse[Any])
async def get_lock_status(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_lock_status(document_id, db=db),
        message="Currently assigned editing manipulation structural lock protocol attributes definitively crosschecked verified",
    )

@router.post("/documents/{document_id}/invite-codes", response_model=APIResponse[Any])
async def generate_invite_code(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.generate_invite_code(document_id, current_user, db=db),
        message="Cryptographically protected access token unlocking group collaborative architectural environment properly generated",
    )

@router.post("/join/{invite_code}", response_model=APIResponse[Any])
async def join_via_invite_code(invite_code: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.join_via_invite_code(invite_code, current_user, db=db),
        message="Validated credential structurally integrating current account navigating secure collaborative group domain",
    )

@router.post("/documents/{document_id}/tasks", response_model=APIResponse[Any])
async def create_task(document_id: str, data: CollabTaskCreateRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.create_task(document_id, data.task_desc, data.assigned_to, current_user, db=db),
        message="Newly defined editorial collaborative operational task systematically incorporated active workflow mapping",
        status=201,
    )

@router.get("/documents/{document_id}/tasks", response_model=APIResponse[Any])
async def get_tasks(document_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_tasks(document_id, current_user, db=db),
        message="Internal structural collection enumerating actively managed analytical team objectives accurately loaded",
    )

@router.patch("/tasks/{task_id}", response_model=APIResponse[Any])
async def update_task(task_id: str, data: UpdateTaskStatusRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.update_task(task_id, data.is_done, current_user, db=db),
        message="Assigned workflow progress functional status updating precise targeted assignment accurately registered",
    )

@router.post("/tasks/{task_id}/comments", response_model=APIResponse[Any])
async def add_task_comment(task_id: str, data: TaskCommentCreateRequest, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.add_task_comment(task_id, data.comment_text, current_user, db=db),
        message="Discussion note systematically attached appending related functional collaborative operational workflow task",
        status=201,
    )

@router.get("/tasks/{task_id}/comments", response_model=APIResponse[Any])
async def get_task_comments(task_id: str, current_user: dict = Depends(require_role(["author"])), db=Depends(get_db)):
    return APIResponse(
        data=await CollaborationService.get_task_comments(task_id, current_user, db=db),
        message="Hierarchical communicative commentary mapping specified editorial operational assignment precisely fetched displaying",
    )