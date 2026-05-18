from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from models.user import UserInDB
from api.dependency import get_current_user, get_current_user_optional, RateLimiter
from services.interaction import InteractionService
from services.document import DocumentService
from services.archive import ArchiveService

router = APIRouter(prefix="/cong-dong")

@router.get("/goi-y-ket-noi", response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=50, period=120))])
async def get_friend_suggestions(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data={"suggestions": await InteractionService.get_friend_suggestions_by_intersection(current_user)}, message="Lấy gợi ý bạn bè thành công", status=status.HTTP_200_OK)

@router.post("/nguoi-dung/{user_id}/nguoi-theo-doi", response_model=APIResponse[Any])
async def toggle_follow(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.toggle_follow(user_id, current_user), message="Cập nhật trạng thái theo dõi thành công", status=status.HTTP_200_OK)

@router.post("/luu-tru", response_model=APIResponse[Any])
async def upload_media(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ArchiveService.upload_media(file, current_user), message="Tải lên tệp đa phương tiện thành công", status=status.HTTP_200_OK)

@router.get("/hashtag-xu-huong", response_model=APIResponse[Any])
async def get_trending_tags(limit: int = Query(10, ge=1, le=50)):
    return APIResponse(data=await DocumentService.get_trending_tags(limit), message="Lấy danh sách hashtag xu hướng thành công", status=status.HTTP_200_OK)

@router.get("/goi-y-tai-lieu", response_model=APIResponse[Any])
async def get_suggested_documents(limit: int = Query(5, ge=1, le=20)):
    return APIResponse(data=await DocumentService.get_suggested_documents(limit), message="Lấy gợi ý tài liệu thành công", status=status.HTTP_200_OK)

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

@router.get("/tim-kiem-nguoi-dung", response_model=APIResponse[Any])
async def search_users(
    q: str = Query(..., min_length=1), 
    limit: int = Query(10, ge=1, le=20),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    return APIResponse(data=await InteractionService.search_users(q, limit, current_user), message="Tìm kiếm người dùng thành công", status=status.HTTP_200_OK)
