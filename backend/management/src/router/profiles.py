import io
import json
from typing import Any
from core.dependency import RateLimiter, get_current_user, get_db
from core.response import APIResponse
from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import StreamingResponse
from src.schemas.users import ProfileUpdate, SettingsUpdate
from src.services.identity import IdentityService
from src.services.privacy import PrivacyService
from src.services.profiles import ProfileService
from src.services.settings import SettingService

router = APIRouter(prefix="/ho-so")

@router.get("/ca-nhan", response_model=APIResponse[Any])
async def get_my_profile(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await ProfileService.get_user_profile(current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.put("/me", response_model=APIResponse[Any])
async def update_my_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await ProfileService.update_profile(data.model_dump(exclude_unset=True), current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.post("/tro-thanh-tac-gia", response_model=APIResponse[Any])
async def become_author(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await IdentityService.become_author(current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.post("/kyc", response_model=APIResponse[Any])
async def upload_kyc(file: UploadFile = File(...), current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await IdentityService.upload_kyc(file, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
        status=status.HTTP_200_OK,
    )

@router.get("/cai-dat", response_model=APIResponse[Any])
async def get_settings(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await SettingService.get_settings(current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.put("/cai-dat", response_model=APIResponse[Any])
async def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await SettingService.update_settings(data.model_dump(exclude_unset=True), current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.get("/ket-xuat-data", response_model=Any, dependencies=[Depends(RateLimiter(calls=2, period=3600))])
async def request_data_export(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    takeout_payload = await PrivacyService.request_data_takeout(current_user, db=db)
    stream = io.BytesIO(json.dumps(takeout_payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"))
    return StreamingResponse(
        stream,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=user_data_export_{current_user.slug}.json"},
    )

@router.get("/{slug}", response_model=APIResponse[Any])
async def get_public_profile(slug: str, db=Depends(get_db)):
    return APIResponse(
        data=await IdentityService.get_public_profile(slug, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )