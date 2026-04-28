from typing import Any
from core.response import APIResponse
from api.dependencies import get_current_user_optional, get_current_user, require_role
from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional
from models.user import UserInDB, RoleEnum
from services.analytics import AnalyticsService
from pydantic import BaseModel

router = APIRouter()

class ReadEvent(BaseModel):
    document_id: str
    chapter_id: str
    time_spent_seconds: int
    is_bounce: bool

@router.get("/dashboard", response_model=APIResponse[Any])
async def get_dashboard_stats(current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN]))) -> Any:
    return APIResponse(data=await AnalyticsService.get_dashboard_stats(current_user), message="Lấy số liệu tổng quan thành công.", status=200)

@router.get("/leaderboard", response_model=APIResponse[Any])
async def get_leaderboard() -> Any:
    return APIResponse(data=await AnalyticsService.get_leaderboard(), message="Lấy bảng xếp hạng thành công.", status=200)

@router.get("/author/stats", response_model=APIResponse[Any])
async def get_author_stats(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await AnalyticsService.get_author_stats(current_user), message="Lấy số liệu tác giả thành công.", status=200)

@router.post("/telemetry/dropoff", response_model=APIResponse[Any])
async def record_funnel_dropoff(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await AnalyticsService.record_funnel_dropoff(payload, current_user), message="Ghi nhận tỷ lệ rơi rớt phễu thành công.", status=200)

@router.get("/documents/{document_id}/entity-profile", response_model=APIResponse[Any])
async def extract_entity_profiling(document_id: str):
    return APIResponse(data=await AnalyticsService.extract_entity_profiling(document_id), message="Trích xuất hồ sơ thực thể thành công.", status=200)

@router.post("/events/read", response_model=APIResponse[Any])
async def log_read_event(event: ReadEvent, current_user: Optional[UserInDB] = Depends(get_current_user_optional)):
    return APIResponse(data=await AnalyticsService.log_read_event(event, current_user), message="Ghi nhận sự kiện đọc tài liệu thành công.", status=200)

@router.get("/authors/demographics", response_model=APIResponse[Any])
async def get_author_demographics(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AnalyticsService.get_author_demographics(current_user), message="Lấy số liệu nhân khẩu học tác giả thành công.", status=200)
