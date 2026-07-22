import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from src.core.dependency import get_current_user, CurrentUser

from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.services.history import HistoryService

router = APIRouter(route_class=LoggingRoute, prefix="/lich-su")

@router.get("", response_model=List[dict])
async def get_user_sessions(
    current_user: CurrentUser = Depends(get_current_user), document_id: Optional[str] = None
):
    return await HistoryService.get_user_sessions(str(current_user.id), document_id)

@router.post("", response_model=Dict[str, Any])
async def create_session(
    data: dict, current_user: CurrentUser = Depends(get_current_user)
):
    data["user_id"] = str(current_user.id)
    return await HistoryService.create_session(data)

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_detail(session_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await HistoryService.get_session_detail(session_id, str(current_user.id))

@router.put("/{session_id}/tieu-de", response_model=Dict[str, Any])
async def update_title(session_id: str, data: dict, current_user: CurrentUser = Depends(get_current_user)):
    return await HistoryService.update_title(session_id, data, str(current_user.id))

@router.delete("/{session_id}", response_model=Dict[str, Any])
async def delete_session(session_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await HistoryService.delete_session(session_id, str(current_user.id))

@router.post("/{session_id}/tin-nhan", response_model=Dict[str, Any])
async def add_message(
    session_id: str,
    data: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    await HistoryService.get_session_detail(session_id, str(current_user.id))
    data["user_id"] = str(current_user.id)
    return await HistoryService.add_message(session_id, data)
