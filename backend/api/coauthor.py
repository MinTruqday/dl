from typing import Any
from shared.core.response import APIResponse
from fastapi import APIRouter, Depends
from shared.models.user import UserInDB
from api.dependency import get_current_user
from services.coauthor import CoauthorService

router = APIRouter(prefix="/dong-tac-gia")

@router.post("/moi/{document_id}", response_model=APIResponse[Any])
async def invite_coauthor(document_id: str, target_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await CoauthorService.invite_coauthor(document_id, target_user_id, current_user), message="Gửi lời mời đồng tác giả thành công", status=201)

@router.get("/loi-moi", response_model=APIResponse[Any])
async def get_my_invites(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await CoauthorService.get_invites(current_user),
        message="Lấy danh sách lời mời cộng tác thành công"
    )
