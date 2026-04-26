from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from typing import List, Optional
from models.user import UserInDB
from models.social import StatusUpdateCreate, StoryCreate
from api.dependencies import get_current_user, get_current_user_optional, RateLimiter
from services.social import SocialService

router = APIRouter(prefix="/social")

@router.get("/intersection-friends", dependencies=[Depends(RateLimiter(calls=50, period=120))])
async def get_friend_suggestions(current_user: UserInDB = Depends(get_current_user)):
    return {"suggestions": await SocialService.get_friend_suggestions_by_intersection(current_user)}

@router.get("/feed")
async def get_feed(
    tab: str = Query("foryou", pattern="^(foryou|following)$"),
    item_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    return await SocialService.get_social_feed(tab, item_type, skip, limit, current_user)

@router.post("/posts", dependencies=[Depends(RateLimiter(calls=10, period=60))])
async def create_post(request: StatusUpdateCreate, current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.create_post(request, current_user)

@router.post("/users/{user_id}/follow")
async def toggle_follow(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.toggle_follow(user_id, current_user)

@router.post("/upload-media")
async def upload_media(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.upload_media(file, current_user)

@router.get("/ranking")
async def get_ranking(limit: int = 5):
    return await SocialService.get_contribution_ranking(limit)

@router.get("/documents/{document_id}/discussions")
async def get_discussions(document_id: str, skip: int = 0, limit: int = 20):
    return await SocialService.get_discussions(document_id, skip, limit)

@router.post("/documents/{document_id}/discussions")
async def create_discussion(document_id: str, data: dict, current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.create_discussion(document_id, data, current_user)

@router.post("/discussions/{discussion_id}/reply")
async def reply_discussion(discussion_id: str, data: dict, current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.reply_discussion(discussion_id, data, current_user)

@router.get("/reader-ranking")
async def get_reader_ranking(limit: int = 5):
    return await SocialService.get_reader_ranking(limit)

@router.post("/posts/{post_id}/report")
async def report_post(post_id: str, reason: str, current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.report_post(post_id, reason, current_user)

@router.get("/trending-tags")
async def get_trending_tags(limit: int = 10):
    return await SocialService.get_trending_tags(limit)

@router.get("/suggested-documents")
async def get_suggested_documents(limit: int = 5):
    return await SocialService.get_suggested_documents(limit)

@router.post("/posts/{post_id}/view")
async def record_post_view(post_id: str):
    return await SocialService.record_post_view(post_id)

@router.post("/posts/{post_id}/save")
async def save_post(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.save_post(post_id, current_user)

@router.get("/saved-posts")
async def get_saved_posts(skip: int = Query(0), limit: int = Query(20), current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.get_saved_posts(current_user, skip, limit)

@router.post("/users/{user_id}/mute")
async def mute_user(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.mute_user(user_id, current_user)

@router.get("/muted-users")
async def get_muted_users(current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.get_muted_users(current_user)

@router.post("/users/{user_id}/block")
async def block_user(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.block_user(user_id, current_user)

@router.get("/blocked-users")
async def get_blocked_users(current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.get_blocked_users(current_user)

@router.get("/polls/{post_id}/voters")
async def get_poll_voters(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await SocialService.get_poll_voters(post_id, current_user)

@router.get("/hashtag/{tag}")
async def get_posts_by_hashtag(tag: str, skip: int = Query(0), limit: int = Query(20), current_user: Optional[UserInDB] = Depends(get_current_user_optional)):
    return await SocialService.get_posts_by_hashtag(tag, skip, limit, current_user)

@router.get("/search-users")
async def search_users(q: str = Query(...), limit: int = Query(10)):
    return await SocialService.search_users(q, limit)
