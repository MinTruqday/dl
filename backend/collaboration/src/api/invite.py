from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import get_db, require_role
from src.schemas.cooperation import CoauthorInviteRequest, CollaborationResponse
from src.services.invite import InviteService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]
OWNER_ROLES = [Role.AUTHOR, Role.ADMIN]

@router.post("/loi-moi", response_model=APIResponse[Any], status_code=201)
async def invite_collaborator(
    data: CoauthorInviteRequest,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await InviteService.send_collaboration_invite(
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
        data=await InviteService.get_my_collaboration_invites(current_user),
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
        data=await InviteService.respond_to_collaboration_invite(
            invite_id, data.status, current_user
        ),
        message="Xử lý phản hồi lời mời cộng tác hoàn tất",
    )

@router.get("/documents/{document_id}/sent-invitations", response_model=APIResponse[Any])
async def get_sent_pending_invites(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await InviteService.get_sent_pending_invites(document_id, current_user),
        message="Trích xuất danh sách lời mời tham gia cộng tác hoàn tất",
    )

@router.delete("/loi-moi/{invite_id}", response_model=APIResponse[Any])
async def revoke_invite(
    invite_id: str,
    current_user: CurrentUser = Depends(require_role(OWNER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await InviteService.revoke_invite(invite_id, current_user),
        message="Hủy bỏ và thu hồi lời mời tham gia cộng tác hoàn tất",
    )
