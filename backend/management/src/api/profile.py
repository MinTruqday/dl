from src.core.dependency import CurrentUser
import io
import json
from typing import Any, Optional

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.services.verification import VerificationService
from src.services.moderation import ModerationService
from src.services.user import UserService
from src.services.configuration import ConfigurationService

from src.core.dependency import RateLimiting, get_current_user, get_db
from src.core.response import APIResponse
from src.schemas.account import ProfileUpdate, SettingsUpdate, UserInDB

router = APIRouter(route_class=LoggingRoute, prefix="/ho-so")

@router.get("/ca-nhan", response_model=APIResponse[Any])
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await UserService.get_user_profile(current_user),
        message="Lấy thông tin người dùng thành công",
        status=200,
    )

@router.put("/ca-nhan", response_model=APIResponse[Any])
async def update_my_profile(
    data: ProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserService.update_profile(
            data.model_dump(exclude_unset=True), current_user
        ),
        message="Cập nhật thông tin hồ sơ thành công",
        status=200,
    )

@router.post("/dang-ky-tac-gia", response_model=APIResponse[Any])
async def apply_author(
    data: Any, current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await VerificationService.apply_author(data, current_user),
        message="Đã gửi yêu cầu đăng ký tác giả",
        status=201,
    )

@router.post("/nang-cap-tac-gia", response_model=APIResponse[Any])
async def become_author(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await VerificationService.become_author(current_user),
        message="Nâng cấp tài khoản tác giả thành công",
        status=200,
    )

@router.post("/xac-minh-danh-tinh", response_model=APIResponse[Any])
async def upload_kyc(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await VerificationService.upload_kyc(file, current_user),
        message="Tải lên tài liệu xác minh danh tính thành công",
        status=status.HTTP_200_OK,
    )

@router.get("/cai-dat", response_model=APIResponse[Any])
async def get_settings(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await ConfigurationService.get_settings(current_user),
        message="Lấy cấu hình thành công",
        status=200,
    )

@router.put("/cai-dat", response_model=APIResponse[Any])
async def update_settings(
    data: SettingsUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ConfigurationService.update_settings(
            data.model_dump(exclude_unset=True), current_user
        ),
        message="Cập nhật cấu hình thành công",
        status=200,
    )

@router.get(
    "/xuat-du-lieu",
    response_model=Any,
    dependencies=[Depends(RateLimiting(calls=2, period=3600))],
)
async def request_data_export(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    takeout_payload = await ModerationService.request_data_takeout(current_user)
    stream = io.BytesIO(
        json.dumps(takeout_payload, ensure_ascii=False, indent=2, default=str).encode(
            "utf-8"
        )
    )
    return StreamingResponse(
        stream,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=user_data_export_{current_user.slug}.json"
        },
    )

@router.post("/chan/{target_id}", response_model=APIResponse[Any])
async def block_user(
    target_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserService.block_user(target_id, current_user),
        message="Hạn chế người dùng thành công",
        status=200,
    )


@router.get("/{slug}", response_model=APIResponse[Any])
async def get_public_profile(slug: str, db=Depends(get_db)):
    return APIResponse(
        data=await VerificationService.get_public_profile(slug),
        message="Lấy hồ sơ công khai thành công",
    )
