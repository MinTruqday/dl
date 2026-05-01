from typing import Any, List
from fastapi import APIRouter, Depends
from api.dependency import require_role
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.collaboration import CollaborationService
from pydantic import BaseModel

router = APIRouter(prefix="/collaboration")

class CoauthorInviteRequest(BaseModel):
    email: str
    role: str = "editor"

class CollaborationResponse(BaseModel):
    status: str

@router.post("/invites", response_model=APIResponse[Any])
async def send_collaboration_invite(document_id: str, data: CoauthorInviteRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.send_collaboration_invite(document_id, data.email, data.role, current_user),
        message="Gửi lời mời cộng tác thành công.",
        status=201
    )

@router.get("/invites", response_model=APIResponse[Any])
async def get_my_collaboration_invites(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.get_my_collaboration_invites(current_user),
        message="Lấy danh sách lời mời thành công."
    )

@router.patch("/invites/{invite_id}", response_model=APIResponse[Any])
async def respond_to_collaboration_invite(invite_id: str, data: CollaborationResponse, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CollaborationService.respond_to_collaboration_invite(invite_id, data.status, current_user),
        message="Đã phản hồi lời mời cộng tác."
    )
