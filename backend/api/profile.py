from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.responses import StreamingResponse
from models.user import UserInDB
from api.dependency import get_current_user, RateLimiter
from services.profile import ProfileService
from pydantic import BaseModel
import json
import io


router = APIRouter(prefix="/profile")

@router.get("/me", response_model=APIResponse[Any])
async def get_my_profile(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.get_user_profile(current_user), message="Lấy thông tin hồ sơ thành công.", status=200)

@router.put("/me", response_model=APIResponse[Any])
async def update_my_profile(data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.update_profile(data, current_user), message="Cập nhật hồ sơ thành công.", status=200)

@router.post("/author-application", response_model=APIResponse[Any])
async def apply_author(data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.apply_author(data, current_user), message="Gửi đơn đăng ký thành công.", status=201)

@router.get("/settings", response_model=APIResponse[Any])
async def get_settings(current_user: UserInDB = Depends(get_current_user)):
    from core.database import db_client
    db = db_client.mongodb.get_default_database()
    user = await db["users"].find_one({"_id": str(current_user.id)}, {"settings": 1})
    defaults = {
        "appearance": "light",
        "fontSize": "medium",
        "notifications": True,
        "privacyProfile": "public",
        "privacyActivity": True,
        "twoFactor": False,
        "notifyCommunity": {"email": True, "inapp": True},
        "notifyFinance": {"email": True, "inapp": True},
        "notifyUpdates": {"email": False, "inapp": True},
        "notifyNewsletter": {"email": True, "inapp": False},
    }
    if user and "settings" in user:
        defaults.update(user["settings"])
    return APIResponse(data=defaults, message="Lấy cài đặt người dùng thành công.", status=200)

@router.put("/settings", response_model=APIResponse[Any])
async def update_settings(data: dict, current_user: UserInDB = Depends(get_current_user)):
    from core.database import db_client
    from datetime import datetime
    db = db_client.mongodb.get_default_database()
    await db["users"].update_one(
        {"_id": str(current_user.id)},
        {"$set": {"settings": data, "updated_at": datetime.utcnow()}}
    )
    return APIResponse(data={"message": "Đã lưu cài đặt."}, message="Lưu cài đặt thành công.", status=200)

@router.get("/takeout", response_model=Any, dependencies=[Depends(RateLimiter(calls=2, period=3600))])
async def request_data_takeout(current_user: UserInDB = Depends(get_current_user)):
    takeout_payload = await ProfileService.request_data_takeout(current_user)
    stream = io.BytesIO(json.dumps(takeout_payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"))
    return StreamingResponse(stream, media_type="application/json", headers={"Content-Disposition": f"attachment; filename=doclib_takeout_{current_user.slug}.json"})




@router.get("/streaks", response_model=APIResponse[Any])
async def get_reading_streaks(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.get_reading_streaks(current_user), message="Lấy thông tin chuỗi ngày đọc thành công.", status=200)

@router.get("/badges", response_model=APIResponse[Any])
async def get_badges(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.get_badges(current_user), message="Lấy danh sách huy hiệu thành công.", status=200)

@router.post("/block/{target_id}", response_model=APIResponse[Any])
async def block_user(target_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ProfileService.block_user(target_id, current_user), message="Đã chặn người dùng này thành công.", status=200)



@router.put("/brand-page", response_model=APIResponse[Any], dependencies=[Depends(get_current_user)])
async def update_brand_page(data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ProfileService.update_brand_page(data, current_user),
        message="Cập nhật trang tác giả thành công."
    )

@router.get("/bookmarks", response_model=APIResponse[Any])
async def get_bookmarks(current_user: UserInDB = Depends(get_current_user)):
    from services.read import ReadService
    return APIResponse(
        data=await ReadService.get_bookmarks(current_user),
        message="Lấy danh sách đánh dấu thành công."
    )

@router.post("/bookmarks/{document_id}", response_model=APIResponse[Any])
async def toggle_bookmark(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    from services.read import ReadService
    return APIResponse(
        data=await ReadService.toggle_bookmark(document_id, current_user),
        message="Đã cập nhật trạng thái lưu trữ."
    )

@router.get("/author/{slug}", response_model=APIResponse[Any])
async def get_author_public_profile(slug: str):
    return APIResponse(
        data=await ProfileService.get_author_public_profile(slug),
        message="Lấy thông tin trang tác giả thành công."
    )
