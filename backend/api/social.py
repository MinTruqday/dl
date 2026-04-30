from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from typing import List, Optional
from models.user import UserInDB
from models.social import StatusUpdateCreate, StoryCreate
from api.dependencies import get_current_user, get_current_user_optional, RateLimiter
from services.social import SocialService

router = APIRouter(prefix="/social")

@router.get("/ai/feed-summary", response_model=APIResponse[Any])
async def get_ai_feed_summary(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data={"summary": await SocialService.generate_ai_feed_summary(current_user)}, message="Tạo tóm tắt bảng tin thành công.", status=status.HTTP_200_OK)

@router.get("/intersection-friends", response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=50, period=120))])
async def get_friend_suggestions(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data={"suggestions": await SocialService.get_friend_suggestions_by_intersection(current_user)}, message="Lấy gợi ý bạn bè thành công.", status=status.HTTP_200_OK)

@router.get("/feed", response_model=APIResponse[Any])
async def get_feed(
    tab: str = Query("foryou", pattern="^(foryou|following)$"),
    item_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    return APIResponse(data=await SocialService.get_social_feed(tab, item_type, skip, limit, current_user), message="Lấy bảng tin thành công.", status=status.HTTP_200_OK)

@router.post("/posts", response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=10, period=60))])
async def create_post(request: StatusUpdateCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.create_post(request, current_user), message="Đăng trạng thái mới thành công.", status=status.HTTP_201_CREATED)

@router.post("/posts/{post_id}/like", response_model=APIResponse[Any])
async def react_to_post(post_id: str, reaction_type: str = Query("like"), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.react_to_post(post_id, reaction_type, current_user), message="Thao tác cảm xúc thành công.", status=status.HTTP_200_OK)

@router.delete("/posts/{post_id}", response_model=APIResponse[Any])
async def delete_post(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.delete_post(post_id, current_user), message="Đã xóa bài viết thành công.", status=status.HTTP_200_OK)

@router.post("/users/{user_id}/follow", response_model=APIResponse[Any])
async def toggle_follow(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.toggle_follow(user_id, current_user), message="Cập nhật trạng thái theo dõi thành công.", status=status.HTTP_200_OK)

@router.post("/upload-media", response_model=APIResponse[Any])
async def upload_media(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.upload_media(file, current_user), message="Tải lên tệp đa phương tiện thành công.", status=status.HTTP_200_OK)

@router.get("/ranking", response_model=APIResponse[Any])
async def get_ranking(limit: int = 5):
    return APIResponse(data=await SocialService.get_contribution_ranking(limit), message="Lấy bảng xếp hạng đóng góp thành công.", status=status.HTTP_200_OK)

@router.get("/documents/{document_id}/discussions", response_model=APIResponse[Any])
async def get_discussions(document_id: str, skip: int = 0, limit: int = 20):
    return APIResponse(data=await SocialService.get_discussions(document_id, skip, limit), message="Lấy danh sách thảo luận thành công.", status=status.HTTP_200_OK)

@router.post("/documents/{document_id}/discussions", response_model=APIResponse[Any])
async def create_discussion(document_id: str, data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.create_discussion(document_id, data, current_user), message="Tạo thảo luận mới thành công.", status=status.HTTP_201_CREATED)

@router.post("/discussions/{discussion_id}/reply", response_model=APIResponse[Any])
async def reply_discussion(discussion_id: str, data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.reply_discussion(discussion_id, data, current_user), message="Phản hồi thảo luận thành công.", status=status.HTTP_201_CREATED)

@router.get("/reader-ranking", response_model=APIResponse[Any])
async def get_reader_ranking(limit: int = 5):
    return APIResponse(data=await SocialService.get_reader_ranking(limit), message="Lấy bảng xếp hạng độc giả thành công.", status=status.HTTP_200_OK)

@router.post("/posts/{post_id}/report", response_model=APIResponse[Any])
async def report_post(post_id: str, reason: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.report_post(post_id, reason, current_user), message="Gửi báo cáo nội dung thành công.", status=status.HTTP_200_OK)

@router.get("/trending-tags", response_model=APIResponse[Any])
async def get_trending_tags(limit: int = 10):
    return APIResponse(data=await SocialService.get_trending_tags(limit), message="Lấy danh sách hashtag xu hướng thành công.", status=status.HTTP_200_OK)

@router.get("/suggested-documents", response_model=APIResponse[Any])
async def get_suggested_documents(limit: int = 5):
    return APIResponse(data=await SocialService.get_suggested_documents(limit), message="Lấy gợi ý tài liệu thành công.", status=status.HTTP_200_OK)

@router.post("/posts/{post_id}/view", response_model=APIResponse[Any])
async def record_post_view(post_id: str):
    return APIResponse(data=await SocialService.record_post_view(post_id), message="Ghi nhận lượt xem trạng thái thành công.", status=status.HTTP_200_OK)

@router.post("/posts/{post_id}/save", response_model=APIResponse[Any])
async def save_post(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.save_post(post_id, current_user), message="Lưu trạng thái thành công.", status=status.HTTP_200_OK)

@router.get("/saved-posts", response_model=APIResponse[Any])
async def get_saved_posts(skip: int = Query(0), limit: int = Query(20), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.get_saved_posts(current_user, skip, limit), message="Lấy danh sách trạng thái đã lưu thành công.", status=status.HTTP_200_OK)

@router.post("/users/{user_id}/mute", response_model=APIResponse[Any])
async def mute_user(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.mute_user(user_id, current_user), message="Tạm ẩn người dùng thành công.", status=status.HTTP_200_OK)

@router.get("/muted-users", response_model=APIResponse[Any])
async def get_muted_users(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.get_muted_users(current_user), message="Lấy danh sách người dùng đang ẩn thành công.", status=status.HTTP_200_OK)

@router.post("/users/{user_id}/block", response_model=APIResponse[Any])
async def block_user(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.block_user(user_id, current_user), message="Chặn người dùng thành công.", status=status.HTTP_200_OK)

@router.get("/blocked-users", response_model=APIResponse[Any])
async def get_blocked_users(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.get_blocked_users(current_user), message="Lấy danh sách người dùng đã chặn thành công.", status=status.HTTP_200_OK)

@router.get("/polls/{post_id}/voters", response_model=APIResponse[Any])
async def get_poll_voters(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.get_poll_voters(post_id, current_user), message="Lấy danh sách người bình chọn thành công.", status=status.HTTP_200_OK)

@router.get("/hashtag/{tag}", response_model=APIResponse[Any])
async def get_posts_by_hashtag(tag: str, skip: int = Query(0), limit: int = Query(20), current_user: Optional[UserInDB] = Depends(get_current_user_optional)):
    return APIResponse(data=await SocialService.get_posts_by_hashtag(tag, skip, limit, current_user), message="Lấy danh sách trạng thái theo hashtag thành công.", status=status.HTTP_200_OK)

@router.get("/search-users", response_model=APIResponse[Any])
async def search_users(q: str = Query(...), limit: int = Query(10)):
    return APIResponse(data=await SocialService.search_users(q, limit), message="Tìm kiếm người dùng thành công.", status=status.HTTP_200_OK)
@router.post("/polls/{post_id}/vote/{option_id}", response_model=APIResponse[Any])
async def vote_poll(post_id: str, option_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SocialService.vote_poll(post_id, option_id, current_user), message="Bình chọn thành công.", status=status.HTTP_200_OK)
