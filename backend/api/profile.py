from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.responses import StreamingResponse
from models.user import UserInDB
from api.dependency import get_current_user, RateLimiter
from services.profile import ProfileService
from services.settings import SettingsService
from services.identity import IdentityService
from services.privacy import PrivacyService
from services.interaction import InteractionService
from services.library import LibraryService
from pydantic import BaseModel
import json
import io

router = APIRouter(prefix="/profile")

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    privacy_mode: Optional[bool] = None

class BrandPageUpdate(BaseModel):
    banner_url: Optional[str] = None
    theme_color: Optional[str] = None
    layout_type: Optional[str] = None

@router.get("/me", response_model=APIResponse[Any])
async def get_my_profile(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.get_user_profile(current_user), message="Lấy thông tin hồ sơ thành công.", status=200)

@router.put("/me", response_model=APIResponse[Any])
async def update_my_profile(data: ProfileUpdate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.update_profile(data.model_dump(exclude_unset=True), current_user), message="Cập nhật hồ sơ thành công.", status=200)

@router.post("/author-applications", response_model=APIResponse[Any])
async def apply_author(data: Any, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await IdentityService.apply_author(data, current_user), message="Gửi đơn đăng ký thành công.", status=201)

@router.get("/settings", response_model=APIResponse[Any])
async def get_settings(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SettingsService.get_settings(current_user), message="Lấy cài đặt người dùng thành công.", status=200)

@router.put("/settings", response_model=APIResponse[Any])
async def update_settings(data: SettingsUpdate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await SettingsService.update_settings(data.model_dump(exclude_unset=True), current_user), message="Lưu cài đặt thành công.", status=200)

@router.get("/export", response_model=Any, dependencies=[Depends(RateLimiter(calls=2, period=3600))])
async def request_data_export(current_user: UserInDB = Depends(get_current_user)):
    takeout_payload = await PrivacyService.request_data_takeout(current_user)
    stream = io.BytesIO(json.dumps(takeout_payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"))
    return StreamingResponse(stream, media_type="application/json", headers={"Content-Disposition": f"attachment; filename=doclib_takeout_{current_user.slug}.json"})

@router.get("/streaks", response_model=APIResponse[Any])
async def get_reading_streaks(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.get_reading_streaks(current_user), message="Lấy thông tin chuỗi ngày đọc thành công.", status=200)

@router.get("/badges", response_model=APIResponse[Any])
async def get_badges(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.get_badges(current_user), message="Lấy danh sách huy hiệu thành công.", status=200)

@router.post("/blocks/{target_id}", response_model=APIResponse[Any])
async def block_user(target_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await InteractionService.block_user(target_id, current_user), message="Đã chặn người dùng này thành công.", status=200)

@router.put("/brand-page", response_model=APIResponse[Any])
async def update_brand_page(data: BrandPageUpdate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ProfileService.update_brand_page(data.model_dump(exclude_unset=True), current_user),
        message="Cập nhật trang tác giả thành công."
    )

@router.get("/bookmarks", response_model=APIResponse[Any])
async def get_bookmarks(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.get_bookmarks(current_user),
        message="Lấy danh sách đánh dấu thành công."
    )

@router.post("/bookmarks/{document_id}", response_model=APIResponse[Any])
async def toggle_bookmark(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.toggle_bookmark(document_id, current_user),
        message="Đã cập nhật trạng thái lưu trữ."
    )

@router.get("/authors/{slug}", response_model=APIResponse[Any])
async def get_author_public_profile(slug: str):
    return APIResponse(
        data=await IdentityService.get_author_public_profile(slug),
        message="Lấy thông tin trang tác giả thành công."
    )
