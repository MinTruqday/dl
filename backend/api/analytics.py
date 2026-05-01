from typing import Any
from fastapi import APIRouter, Depends
from api.dependencies import require_role
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.analytics import AnalyticsService
from pydantic import BaseModel

router = APIRouter(prefix="/analytics")

@router.get("/system", response_model=APIResponse[Any])
async def get_system_stats(current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN]))):
    return APIResponse(
        data=await AnalyticsService.get_dashboard_stats(current_user),
        message="Lấy số liệu hệ thống thành công."
    )

@router.get("/leaderboard", response_model=APIResponse[Any])
async def get_leaderboard():
    return APIResponse(
        data=await AnalyticsService.get_leaderboard(),
        message="Lấy bảng xếp hạng thành công."
    )

@router.get("/revenue", response_model=APIResponse[Any])
async def get_author_revenue(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await AnalyticsService.get_author_revenue_analytics(current_user),
        message="Lấy số liệu doanh thu thành công."
    )

@router.get("/documents/{document_id}/dropoff", response_model=APIResponse[Any])
async def get_document_dropoff(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await AnalyticsService.get_chapter_dropoff(document_id, current_user),
        message="Lấy tỷ lệ rơi rớt độc giả thành công."
    )

@router.get("/documents/{document_id}/sentiment", response_model=APIResponse[Any])
async def get_reader_sentiment(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await AnalyticsService.analyze_reader_sentiment(document_id, current_user),
        message="Phân tích cảm xúc độc giả thành công."
    )
