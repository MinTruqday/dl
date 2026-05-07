from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from typing import Optional
from models.user import UserInDB
from models.social import StoryCreate
from api.dependency import get_current_user, get_current_user_optional, RateLimiter
from services.story import StoryService

router = APIRouter(prefix="/cau-chuyen")

@router.get("", response_model=APIResponse[Any])
async def list_stories(current_user: Optional[UserInDB] = Depends(get_current_user_optional)):
    return APIResponse(data=await StoryService.list_stories(current_user), message="Lấy danh sách tin tức thành công", status=200)

@router.post("", response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=10, period=60))])
async def create_story(request: StoryCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.create_story(request, current_user), message="Đăng tin tức thành công", status=201)

@router.get("/ca-nhan", response_model=APIResponse[Any])
async def get_my_stories(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.get_my_stories(current_user), message="Lấy danh sách tin tức của bạn thành công", status=200)

@router.get("/ca-nhan/luu-tru", response_model=APIResponse[Any])
async def get_archived_stories(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.get_archived_stories(current_user), message="Lấy kho lưu trữ tin tức thành công", status=200)

@router.post("/{story_id}/xem", response_model=APIResponse[Any])
async def record_view(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.record_view(story_id, current_user), message="Đã ghi nhận lượt xem tin tức", status=200)

@router.get("/{story_id}/nguoi-xem", response_model=APIResponse[Any])
async def get_story_viewers(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.get_story_viewers(story_id, current_user), message="Lấy danh sách người xem thành công", status=200)

@router.post("/{story_id}/cam-xuc", response_model=APIResponse[Any])
async def react_to_story(
    story_id: str,
    reaction_type: str = Query("heart", pattern="^(heart|fire|wow|sad)$"),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await StoryService.react_to_story(story_id, reaction_type, current_user), message="Thả cảm xúc thành công", status=200)

@router.post("/{story_id}/khao-sat/binh-chon", response_model=APIResponse[Any])
async def vote_story_poll(
    story_id: str,
    option_index: int = Query(., ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await StoryService.vote_story_poll(story_id, option_index, current_user), message="Bình chọn thành công", status=200)

@router.post("/{story_id}/do-vui/tra-loi", response_model=APIResponse[Any])
async def answer_story_quiz(
    story_id: str,
    option_index: int = Query(., ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await StoryService.answer_story_quiz(story_id, option_index, current_user), message="Trả lời câu hỏi thành công", status=200)

@router.post("/{story_id}/phan-hoi", response_model=APIResponse[Any])
async def reply_to_story(
    story_id: str,
    message: str = Query(., min_length=1, max_length=500),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await StoryService.reply_to_story(story_id, message, current_user), message="Phản hồi tin tức thành công", status=201)

@router.post("/{story_id}/luu-tru", response_model=APIResponse[Any])
async def archive_story(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.archive_story(story_id, current_user), message="Đã đưa tin tức vào kho lưu trữ", status=200)

@router.delete("/{story_id}", response_model=APIResponse[Any])
async def delete_story(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await StoryService.delete_story(story_id, current_user), message="Xóa tin tức thành công", status=200)
