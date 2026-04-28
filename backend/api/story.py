from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from typing import Optional
from models.user import UserInDB
from models.social import StoryCreate
from api.dependencies import get_current_user, get_current_user_optional, RateLimiter
from services.story import StoryService

router = APIRouter(prefix="/social/stories")

@router.get("", response_model=APIResponse[Any])
async def list_stories(current_user: Optional[UserInDB] = Depends(get_current_user_optional)):
    return APIResponse(data=await StoryService.list_stories(current_user), message="Lấy danh sách tin tức thành công.", status=200)

@router.post("", response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=10, period=60))])
async def create_story(request: StoryCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.create_story(request, current_user), message="Đăng tin tức thành công.", status=201)

@router.get("/me", response_model=APIResponse[Any])
async def get_my_stories(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.get_my_stories(current_user), message="Lấy danh sách tin tức của bạn thành công.", status=200)

@router.get("/me/archive", response_model=APIResponse[Any])
async def get_archived_stories(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.get_archived_stories(current_user), message="Lấy kho lưu trữ tin tức thành công.", status=200)

@router.post("/{story_id}/view", response_model=APIResponse[Any])
async def record_view(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.record_view(story_id, current_user), message="Đã ghi nhận lượt xem tin tức.", status=200)

@router.get("/{story_id}/viewers", response_model=APIResponse[Any])
async def get_story_viewers(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.get_story_viewers(story_id, current_user), message="Lấy danh sách người xem thành công.", status=200)

@router.post("/{story_id}/react", response_model=APIResponse[Any])
async def react_to_story(
    story_id: str,
    reaction_type: str = Query("heart", pattern="^(heart|fire|wow|sad)$"),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await StoryService.react_to_story(story_id, reaction_type, current_user), message="Thả cảm xúc thành công.", status=200)

@router.post("/{story_id}/poll/vote", response_model=APIResponse[Any])
async def vote_story_poll(
    story_id: str,
    option_index: int = Query(..., ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await StoryService.vote_story_poll(story_id, option_index, current_user), message="Bình chọn thành công.", status=200)

@router.post("/{story_id}/quiz/answer", response_model=APIResponse[Any])
async def answer_story_quiz(
    story_id: str,
    option_index: int = Query(..., ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await StoryService.answer_story_quiz(story_id, option_index, current_user), message="Trả lời câu hỏi thành công.", status=200)

@router.post("/{story_id}/reply", response_model=APIResponse[Any])
async def reply_to_story(
    story_id: str,
    message: str = Query(..., min_length=1, max_length=500),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await StoryService.reply_to_story(story_id, message, current_user), message="Phản hồi tin tức thành công.", status=201)

@router.post("/{story_id}/archive", response_model=APIResponse[Any])
async def archive_story(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.archive_story(story_id, current_user), message="Đã đưa tin tức vào kho lưu trữ.", status=200)

@router.delete("/{story_id}", response_model=APIResponse[Any])
async def delete_story(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.delete_story(story_id, current_user), message="Xóa tin tức thành công.", status=200)
