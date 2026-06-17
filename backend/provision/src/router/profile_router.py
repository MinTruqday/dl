from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.responses import StreamingResponse
from core.schemas.user import UserInDB, ProfileUpdate, SettingsUpdate, BrandPageUpdate
from core.dependency import get_db, get_current_user, RateLimiter
from src.services.profile_service import ProfileService
from src.services.setting_service import SettingService
from src.services.identity_service import IdentityService
from src.services.privacy_service import PrivacyService
from pydantic import BaseModel
import json
import io

router = APIRouter(prefix="/profiles")


@router.get("/me", response_model=APIResponse[Any])
async def get_my_profile(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await ProfileService.get_user_profile(current_user, db=db),
        message="The requested user profile information has been successfully retrieved from the database",
        status=200,
    )


@router.put("/me", response_model=APIResponse[Any])
async def update_my_profile(
    data: ProfileUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ProfileService.update_profile(
            data.model_dump(exclude_unset=True), current_user, db=db
        ),
        message="The user profile information has been successfully updated and saved",
        status=200,
    )


@router.post("/applications/author", response_model=APIResponse[Any])
async def apply_author(
    data: Any, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await IdentityService.apply_author(data, current_user, db=db),
        message="The author application has been successfully submitted and is pending administrative review",
        status=201,
    )


@router.post("/upgrade-to-author", response_model=APIResponse[Any])
async def become_author(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await IdentityService.become_author(current_user, db=db),
        message="The user account privileges have been successfully elevated to author status",
        status=200,
    )


@router.post("/kyc", response_model=APIResponse[Any])
async def upload_kyc(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await IdentityService.upload_kyc(file, current_user, db=db),
        message="The identity verification documents have been securely uploaded and are awaiting review",
        status=status.HTTP_200_OK,
    )


@router.get("/settings", response_model=APIResponse[Any])
async def get_settings(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await SettingService.get_settings(current_user, db=db),
        message="The system configuration settings have been successfully retrieved",
        status=200,
    )


@router.put("/settings", response_model=APIResponse[Any])
async def update_settings(
    data: SettingsUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SettingService.update_settings(
            data.model_dump(exclude_unset=True), current_user, db=db
        ),
        message="The system configuration settings have been successfully updated and applied",
        status=200,
    )


@router.get(
    "/export-data",
    response_model=Any,
    dependencies=[Depends(RateLimiter(calls=2, period=3600))],
)
async def request_data_export(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    takeout_payload = await PrivacyService.request_data_takeout(current_user, db=db)
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


@router.get("/reading-streaks", response_model=APIResponse[Any])
async def get_reading_streaks(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await ProfileService.get_reading_streaks(current_user, db=db),
        message="The reading streak statistics for the current user have been successfully retrieved",
        status=200,
    )


@router.get("/badges", response_model=APIResponse[Any])
async def get_badges(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await ProfileService.get_badges(current_user, db=db),
        message="The list of earned badges has been successfully retrieved from the system",
        status=200,
    )


@router.post("/block/{target_id}", response_model=APIResponse[Any])
async def block_user(
    target_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ProfileService.block_user(target_id, current_user, db=db),
        message="The specified user has been successfully restricted from interacting with your account",
        status=200,
    )


@router.put("/brand-page", response_model=APIResponse[Any])
async def update_brand_page(
    data: BrandPageUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await ProfileService.update_brand_page(
            data.model_dump(exclude_unset=True), current_user, db=db
        ),
        message="The public author brand page has been successfully updated with the provided information",
    )


@router.get("/{slug}", response_model=APIResponse[Any])
async def get_public_profile(slug: str, db=Depends(get_db)):
    return APIResponse(
        data=await IdentityService.get_public_profile(slug, db=db),
        message="The public profile information for the specified user has been successfully retrieved",
    )