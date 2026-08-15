from typing import Any
from fastapi import APIRouter, Depends, Query, status
from src.core.response import APIResponse
from src.api.dependency import get_current_user_optional, get_db, CurrentUser
from src.services.discovery import DiscoveryService

router = APIRouter(prefix="/kham-pha")

@router.get("/the-loai", response_model=APIResponse[Any])
async def get_tags_categories(db=Depends(get_db)):
    return APIResponse(
        data=await DiscoveryService.get_tags_categories(),
        message="Trích xuất danh sách thẻ và danh mục hệ thống hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.get("/goi-y-ca-nhan", response_model=APIResponse[Any])
async def get_personalized_recommendations(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    if current_user:
        recommendations = await DiscoveryService.get_personalized_recommendations(
            str(current_user.id),
            limit,
        )
        if recommendations:
            return APIResponse(
                data=recommendations,
                message="Trích xuất danh sách khuyến nghị cá nhân hóa hoàn tất",
            )
    return APIResponse(
        data=await DiscoveryService.get_trending_documents(limit),
        message="Chưa đủ lịch sử đọc để cá nhân hóa nên hệ thống trả tài liệu thịnh hành",
    )
