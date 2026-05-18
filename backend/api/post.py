from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, status
from models.user import UserInDB
from models.social import StatusUpdateCreate, ReportCreate, ExcerptShareRequest
from api.dependency import get_current_user, get_current_user_optional, RateLimiter
from services.post import PostService
from services.interaction import InteractionService

router = APIRouter(prefix="/cong-dong")

@router.get("/bang-tin", response_model=APIResponse[Any])
async def get_feed(
    tab: str = Query("foryou", pattern="^(foryou|following)$"),
    item_type: Optional[str] = Query(None),
    cursor: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    return APIResponse(data=await PostService.get_social_feed(tab, item_type, limit, current_user, cursor), message="Lấy bảng tin thành công", status=status.HTTP_200_OK)

@router.post("/bai-viet", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(calls=10, period=60))])
async def create_post(request: StatusUpdateCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.create_post(request, current_user), message="Đăng trạng thái mới thành công", status=status.HTTP_201_CREATED)

@router.put("/bai-viet/{post_id}", response_model=APIResponse[Any])
async def update_post(post_id: str, request: StatusUpdateCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.update_post(post_id, request.content, current_user), message="Cập nhật bài viết thành công", status=status.HTTP_200_OK)

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

@router.post("/bai-viet/{post_id}/bao-cao", response_model=APIResponse[Any])
async def report_post(post_id: str, req: ReportCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.report_post(post_id, req.reason, current_user), message="Gửi báo cáo nội dung thành công", status=status.HTTP_200_OK)

@router.post("/bai-viet/{post_id}/luot-xem", response_model=APIResponse[Any])
async def record_post_view(post_id: str):
    return APIResponse(data=await PostService.record_post_view(post_id), message="Ghi nhận lượt xem trạng thái thành công", status=status.HTTP_200_OK)

@router.post("/bai-viet/{post_id}/luu-lai", response_model=APIResponse[Any])
async def save_post(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.save_post(post_id, current_user), message="Lưu trạng thái thành công", status=status.HTTP_200_OK)

@router.get("/bai-viet-da-luu", response_model=APIResponse[Any])
async def get_saved_posts(cursor: str = None, limit: int = Query(20, ge=1, le=50), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.get_saved_posts(current_user, cursor, limit), message="Lấy danh sách trạng thái đã lưu thành công", status=status.HTTP_200_OK)

@router.get("/khao-sat/{post_id}/nguoi-binh-chon", response_model=APIResponse[Any])
async def get_poll_voters(post_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.get_poll_voters(post_id, current_user), message="Lấy danh sách người bình chọn thành công", status=status.HTTP_200_OK)

@router.get("/the-tag/{tag}", response_model=APIResponse[Any])
async def get_posts_by_hashtag(tag: str, cursor: str = None, limit: int = Query(20, ge=1, le=50), current_user: Optional[UserInDB] = Depends(get_current_user_optional)):
    return APIResponse(data=await PostService.get_posts_by_hashtag(tag, cursor, limit, current_user), message="Lấy danh sách trạng thái theo hashtag thành công", status=status.HTTP_200_OK)

@router.post("/khao-sat/{post_id}/binh-chon/{option_id}", response_model=APIResponse[Any])
async def vote_poll(post_id: str, option_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PostService.vote_poll(post_id, option_id, current_user), message="Bình chọn thành công", status=status.HTTP_200_OK)

@router.post("/chia-se-trich-doan", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
async def share_excerpt(payload: ExcerptShareRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PostService.share_excerpt(payload.model_dump(), current_user), 
        message="Chia sẻ trích đoạn thành công", 
        status=status.HTTP_201_CREATED
    )
