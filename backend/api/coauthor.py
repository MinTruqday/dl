from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from models.user import UserInDB
from api.dependency import get_current_user
from services.coauthor import CoauthorService

router = APIRouter(prefix="/coauthor")

@router.post("/invite/{document_id}", response_model=APIResponse[Any])
async def invite_coauthor(document_id: str, target_user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await CoauthorService.invite_coauthor(document_id, target_user_id, current_user), message="Gửi lời mời đồng tác giả thành công.", status=201)
