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

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN]))) -> Any:
    return await AnalyticsService.get_dashboard_stats(current_user)

@router.get("/leaderboard")
async def get_leaderboard() -> Dict[str, Any]:
    return await AnalyticsService.get_leaderboard()

@router.get("/author/stats")
async def get_author_stats(current_user: UserInDB = Depends(get_current_user)):
    return await AnalyticsService.get_author_stats(current_user)

@router.post("/telemetry/dropoff")
async def record_funnel_dropoff(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return await AnalyticsService.record_funnel_dropoff(payload, current_user)

@router.get("/documents/{document_id}/entity-profile")
async def extract_entity_profiling(document_id: str):
    return await AnalyticsService.extract_entity_profiling(document_id)

@router.post("/events/read")
async def log_read_event(event: ReadEvent, current_user: Optional[UserInDB] = Depends(get_current_user_optional)):
    return await AnalyticsService.log_read_event(event, current_user)

@router.get("/authors/demographics")
async def get_author_demographics(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AnalyticsService.get_author_demographics(current_user)
