from typing import Any, List, Optional
from shared.core.response import APIResponse
from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from shared.models.user import UserInDB
from shared.models.social import StatusUpdateCreate, DiscussionCreate, DiscussionReply, ReportCreate
from api.dependency import get_current_user, get_current_user_optional, RateLimiter, require_permissions
from services.post import PostService
from services.interaction import InteractionService
from services.discussion import DiscussionService
from services.feed import FeedService
from services.rank import RankService
from services.asset import AssetService
router = APIRouter(prefix="/cong-dong")
@router.get("/ai/tom-tat-bang-tin", response_model=APIResponse[Any])
async def get_ai_feed_summary(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data={"summary": await FeedService.generate_ai_feed_summary(current_user)}, message="Tạo tóm tắt bảng tin thành công", status=status.HTTP_200_OK)
@router.get("/goi-y-ket-noi", response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=50, period=120))])
async def get_friend_suggestions(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data={"suggestions": await FeedService.get_friend_suggestions_by_intersection(current_user)}, message="Lấy gợi ý bạn bè thành công", status=status.HTTP_200_OK)
@router.get("/bang-tin", response_model=APIResponse[Any])
async def get_feed(
    tab: str = Query("foryou", pattern="^(foryou|following)$"),
    item_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    return APIResponse(data=await FeedService.get_social_feed(tab, item_type, skip, limit, current_user), message="Lấy bảng tin thành công", status=status.HTTP_200_OK)
@router.post("/bai-viet", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(calls=10, period=60))])
async def create_post(request: StatusUpdateCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.create_post(request, current_user), message="Đăng trạng thái mới thành công", status=status.HTTP_201_CREATED)
@router.post("/bai-viet/{post_id}/cam-xuc", response_model=APIResponse[Any])
async def react_to_post(post_id: str, reaction_type: str = Query("like"), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.react_to_post(post_id, reaction_type, current_user), message="Thao tác cảm xúc thành công", status=status.HTTP_200_OK)
@router.delete("/bai-viet/{post_id}", response_model=APIResponse[Any])
async def delete_post(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.delete_post(post_id, current_user), message="Đã xóa bài viết thành công", status=status.HTTP_200_OK)
@router.post("/bai-viet/{post_id}/chia-se-lai", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
async def repost_post(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.repost_post(post_id, current_user), message="Đã chia sẻ lại bài viết thành công", status=status.HTTP_201_CREATED)
@router.post("/bai-viet/{post_id}/ghim", response_model=APIResponse[Any])
async def toggle_pin_post(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.toggle_pin_post(post_id, current_user), message="Đã cập nhật trạng thái ghim", status=status.HTTP_200_OK)
@router.post("/bai-viet/{post_id}/an", response_model=APIResponse[Any])
async def hide_post(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.hide_post(post_id, current_user), message="Đã ẩn bài viết thành công", status=status.HTTP_200_OK)
@router.post("/nguoi-dung/{user_id}/nguoi-theo-doi", response_model=APIResponse[Any])
async def toggle_follow(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.toggle_follow(user_id, current_user), message="Cập nhật trạng thái theo dõi thành công", status=status.HTTP_200_OK)
@router.post("/tai-nguyen", response_model=APIResponse[Any])
async def upload_media(file: UploadFile = File(.), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await AssetService.upload_media(file, current_user), message="Tải lên tệp đa phương tiện thành công", status=status.HTTP_200_OK)
@router.get("/xep-hang", response_model=APIResponse[Any])
async def get_ranking(limit: int = Query(5, ge=1, le=50)):
    return APIResponse(data=await RankService.get_contribution_ranking(limit), message="Lấy bảng xếp hạng đóng góp thành công", status=status.HTTP_200_OK)
@router.get("/tai-lieu/{document_id}/thao-luan", response_model=APIResponse[Any])
async def get_discussions(document_id: str, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)):
    return APIResponse(data=await DiscussionService.get_discussions(document_id, skip, limit), message="Lấy danh sách thảo luận thành công", status=status.HTTP_200_OK)
@router.post("/tai-lieu/{document_id}/thao-luan", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
async def create_discussion(document_id: str, data: DiscussionCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DiscussionService.create_discussion(document_id, data.model_dump(), current_user), message="Tạo thảo luận mới thành công", status=status.HTTP_201_CREATED)
@router.post("/thao-luan/{discussion_id}/phan-hoi", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
async def reply_discussion(discussion_id: str, data: DiscussionReply, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DiscussionService.reply_discussion(discussion_id, data.model_dump(), current_user), message="Phản hồi thảo luận thành công", status=status.HTTP_201_CREATED)
@router.get("/xep-hang-doc-gia", response_model=APIResponse[Any])
async def get_reader_ranking(limit: int = Query(5, ge=1, le=50)):
    return APIResponse(data=await RankService.get_reader_ranking(limit), message="Lấy bảng xếp hạng độc giả thành công", status=status.HTTP_200_OK)
@router.post("/bai-viet/{post_id}/bao-cao", response_model=APIResponse[Any])
async def report_post(post_id: str, req: ReportCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.report_post(post_id, req.reason, current_user), message="Gửi báo cáo nội dung thành công", status=status.HTTP_200_OK)
@router.get("/hashtag-xu-huong", response_model=APIResponse[Any])
async def get_trending_tags(limit: int = Query(10, ge=1, le=50)):
    return APIResponse(data=await FeedService.get_trending_tags(limit), message="Lấy danh sách hashtag xu hướng thành công", status=status.HTTP_200_OK)
@router.get("/goi-y-tai-lieu", response_model=APIResponse[Any])
async def get_suggested_documents(limit: int = Query(5, ge=1, le=20)):
    return APIResponse(data=await FeedService.get_suggested_documents(limit), message="Lấy gợi ý tài liệu thành công", status=status.HTTP_200_OK)
@router.post("/bai-viet/{post_id}/luot-xem", response_model=APIResponse[Any])
async def record_post_view(post_id: str):
    return APIResponse(data=await PostService.record_post_view(post_id), message="Ghi nhận lượt xem trạng thái thành công", status=status.HTTP_200_OK)
@router.post("/bai-viet/{post_id}/luu-lai", response_model=APIResponse[Any])
async def save_post(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.save_post(post_id, current_user), message="Lưu trạng thái thành công", status=status.HTTP_200_OK)
@router.get("/bai-viet-da-luu", response_model=APIResponse[Any])
async def get_saved_posts(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.get_saved_posts(current_user, skip, limit), message="Lấy danh sách trạng thái đã lưu thành công", status=status.HTTP_200_OK)
@router.post("/nguoi-dung/{user_id}/tam-an", response_model=APIResponse[Any])
async def mute_user(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.mute_user(user_id, current_user), message="Tạm ẩn người dùng thành công", status=status.HTTP_200_OK)
@router.get("/nguoi-dung-tam-an", response_model=APIResponse[Any])
async def get_muted_users(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.get_muted_users(current_user), message="Lấy danh sách người dùng đang ẩn thành công", status=status.HTTP_200_OK)
@router.post("/nguoi-dung/{user_id}/chan", response_model=APIResponse[Any])
async def block_user(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.block_user(user_id, current_user), message="Chặn người dùng thành công", status=status.HTTP_200_OK)
@router.get("/nguoi-dung-bi-chan", response_model=APIResponse[Any])
async def get_blocked_users(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.get_blocked_users(current_user), message="Lấy danh sách người dùng đã chặn thành công", status=status.HTTP_200_OK)
@router.get("/khao-sat/{post_id}/nguoi-binh-chon", response_model=APIResponse[Any])
async def get_poll_voters(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.get_poll_voters(post_id, current_user), message="Lấy danh sách người bình chọn thành công", status=status.HTTP_200_OK)
@router.get("/the-tag/{tag}", response_model=APIResponse[Any])
async def get_posts_by_hashtag(tag: str, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50), current_user: Optional[UserInDB] = Depends(get_current_user_optional)):
    return APIResponse(data=await PostService.get_posts_by_hashtag(tag, skip, limit, current_user), message="Lấy danh sách trạng thái theo hashtag thành công", status=status.HTTP_200_OK)
@router.get("/tim-kiem-nguoi-dung", response_model=APIResponse[Any])
async def search_users(q: str = Query(., min_length=1), limit: int = Query(10, ge=1, le=20)):
    return APIResponse(data=await FeedService.search_users(q, limit), message="Tìm kiếm người dùng thành công", status=status.HTTP_200_OK)
@router.post("/khao-sat/{post_id}/binh-chon/{option_id}", response_model=APIResponse[Any])
async def vote_poll(post_id: str, option_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.vote_poll(post_id, option_id, current_user), message="Bình chọn thành công", status=status.HTTP_200_OK)
@router.post("/chia-se-trich-doan", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
async def share_excerpt(data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PostService.share_excerpt(data, current_user), 
        message="Chia sẻ trích đoạn thành công", 
        status=status.HTTP_201_CREATED
    )
@router.get("/tac-gia-noi-bat", response_model=APIResponse[Any])
async def get_featured_authors(limit: int = Query(10, ge=1, le=50)):
    return APIResponse(
        data=await RankService.get_featured_authors(limit),
        message="Lấy danh sách tác giả nổi bật thành công"
    )
@router.get("/tai-lieu/{document_id}/cam-quan", response_model=APIResponse[Any], dependencies=[Depends(require_permissions(["documents:read_any"]))])
async def get_reader_sentiment(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=None,
        message="Tính năng phân tích cảm nhận độc giả đang được phát triển"
    )
