from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, status
from models.user import UserInDB
from models.social import DiscussionCreate, DiscussionReply
from api.dependency import get_current_user, get_current_user_optional
from services.discussion import DiscussionService

router = APIRouter(prefix="/cong-dong")

@router.get("/tai-lieu/{document_id}/thao-luan", response_model=APIResponse[Any])
async def get_discussions(
    document_id: str, 
    cursor: str = None, 
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    return APIResponse(data=await DiscussionService.get_discussions(document_id, cursor, limit, current_user), message="Lấy danh sách thảo luận thành công", status=status.HTTP_200_OK)

@router.post("/tai-lieu/{document_id}/thao-luan", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
async def create_discussion(document_id: str, data: DiscussionCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DiscussionService.create_discussion(document_id, data.model_dump(), current_user), message="Tạo thảo luận mới thành công", status=status.HTTP_201_CREATED)

@router.post("/thao-luan/{discussion_id}/phan-hoi", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
async def reply_discussion(discussion_id: str, data: DiscussionReply, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DiscussionService.reply_discussion(discussion_id, data.model_dump(), current_user), message="Phản hồi thảo luận thành công", status=status.HTTP_201_CREATED)
