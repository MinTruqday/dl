from fastapi import APIRouter, Depends, Query
from typing import Optional
from models.user import UserInDB
from models.social import StoryCreate
from api.dependencies import get_current_user, get_current_user_optional, RateLimiter
from services.story import StoryService

router = APIRouter(prefix="/social/stories")

@router.get("")
async def list_stories(current_user: Optional[UserInDB] = Depends(get_current_user_optional)):
    return await StoryService.list_stories(current_user)

@router.post("", dependencies=[Depends(RateLimiter(calls=10, period=60))])
async def create_story(request: StoryCreate, current_user: UserInDB = Depends(get_current_user)):
    return await StoryService.create_story(request, current_user)

@router.get("/me")
async def get_my_stories(current_user: UserInDB = Depends(get_current_user)):
    return await StoryService.get_my_stories(current_user)

@router.get("/me/archive")
async def get_archived_stories(current_user: UserInDB = Depends(get_current_user)):
    return await StoryService.get_archived_stories(current_user)

@router.post("/{story_id}/view")
async def record_view(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await StoryService.record_view(story_id, current_user)

@router.get("/{story_id}/viewers")
async def get_story_viewers(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await StoryService.get_story_viewers(story_id, current_user)

@router.post("/{story_id}/react")
async def react_to_story(
    story_id: str,
    reaction_type: str = Query("heart", pattern="^(heart|fire|wow|sad)$"),
    current_user: UserInDB = Depends(get_current_user)
):
    return await StoryService.react_to_story(story_id, reaction_type, current_user)

@router.post("/{story_id}/poll/vote")
async def vote_story_poll(
    story_id: str,
    option_index: int = Query(..., ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    return await StoryService.vote_story_poll(story_id, option_index, current_user)

@router.post("/{story_id}/quiz/answer")
async def answer_story_quiz(
    story_id: str,
    option_index: int = Query(..., ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    return await StoryService.answer_story_quiz(story_id, option_index, current_user)

@router.post("/{story_id}/reply")
async def reply_to_story(
    story_id: str,
    message: str = Query(..., min_length=1, max_length=500),
    current_user: UserInDB = Depends(get_current_user)
):
    return await StoryService.reply_to_story(story_id, message, current_user)

@router.post("/{story_id}/archive")
async def archive_story(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await StoryService.archive_story(story_id, current_user)

@router.delete("/{story_id}")
async def delete_story(story_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await StoryService.delete_story(story_id, current_user)
