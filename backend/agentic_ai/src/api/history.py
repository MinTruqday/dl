from typing import Any, Dict, List, Optional

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from src.core.dependency import get_current_user, CurrentUser


from src.services.history import HistoryService

router = APIRouter(route_class=LoggingRoute, prefix="/lich-su")

@router.get("", response_model=List[dict])
async def get_user_sessions(
    current_user: CurrentUser = Depends(get_current_user), document_id: Optional[str] = None
):
    """List conversation sessions owned by the authenticated user"""
    return await HistoryService.get_user_sessions(str(current_user.id), document_id)

@router.post("", response_model=Dict[str, Any])
async def create_session(
    data: dict, current_user: CurrentUser = Depends(get_current_user)
):
    """Create a conversation session for the authenticated user"""
    data["user_id"] = str(current_user.id)
    return await HistoryService.create_session(data)

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_detail(session_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """Return one owned conversation session with its messages"""
    return await HistoryService.get_session_detail(session_id, str(current_user.id))

@router.put("/{session_id}/tieu-de", response_model=Dict[str, Any])
async def update_title(session_id: str, data: dict, current_user: CurrentUser = Depends(get_current_user)):
    """Update the title of an owned conversation session"""
    return await HistoryService.update_title(session_id, data, str(current_user.id))

@router.delete("/{session_id}", response_model=Dict[str, Any])
async def delete_session(session_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """Delete an owned conversation session and its stored messages"""
    return await HistoryService.delete_session(session_id, str(current_user.id))

@router.post("/{session_id}/tin-nhan", response_model=Dict[str, Any])
async def add_message(
    session_id: str,
    data: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Append one message to an owned conversation session"""
    await HistoryService.get_session_detail(session_id, str(current_user.id))
    data["user_id"] = str(current_user.id)
    return await HistoryService.add_message(session_id, data)
