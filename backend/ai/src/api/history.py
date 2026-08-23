from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.dependency import get_current_user, CurrentUser


from src.services.history import HistoryService
from src.schemas.history import MessageCreate, SessionCreate, SessionStateUpdate, SessionTitleUpdate

router = APIRouter(prefix="/lich-su")


@router.get("", response_model=List[dict])
async def get_user_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    document_id: Optional[str] = Query(default=None, min_length=1, max_length=128),
    skip: int = Query(default=0, ge=0, le=100000),
    limit: int = Query(default=100, ge=1, le=100),
):
    """List conversation sessions owned by the authenticated user"""
    return await HistoryService.get_user_sessions(str(current_user.id), document_id, skip, limit)


@router.post("", response_model=Dict[str, Any])
async def create_session(
    data: SessionCreate, current_user: CurrentUser = Depends(get_current_user)
):
    """Create a conversation session for the authenticated user"""
    payload = data.model_dump()
    payload["user_id"] = str(current_user.id)
    return await HistoryService.create_session(payload)


@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_detail(
    session_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    """Return one owned conversation session with its messages"""
    return await HistoryService.get_session_detail(session_id, str(current_user.id))


@router.put("/{session_id}/tieu-de", response_model=Dict[str, Any])
async def update_title(
    session_id: str, data: SessionTitleUpdate, current_user: CurrentUser = Depends(get_current_user)
):
    """Update the title of an owned conversation session"""
    return await HistoryService.update_title(session_id, data.model_dump(), str(current_user.id))


@router.patch("/{session_id}/trang-thai", response_model=Dict[str, Any])
async def update_state(
    session_id: str, data: SessionStateUpdate, current_user: CurrentUser = Depends(get_current_user)
):
    """Update the pinned or archived state of an owned conversation session."""
    return await HistoryService.update_state(session_id, data.model_dump(), str(current_user.id))


@router.delete("/{session_id}", response_model=Dict[str, Any])
async def delete_session(session_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """Delete an owned conversation session and its stored messages"""
    return await HistoryService.delete_session(session_id, str(current_user.id))


@router.post("/{session_id}/luot", response_model=Dict[str, Any])
async def add_message(
    session_id: str, data: MessageCreate, current_user: CurrentUser = Depends(get_current_user)
):
    """Append one message to an owned conversation session"""
    await HistoryService.get_session_detail(session_id, str(current_user.id))
    payload = data.model_dump()
    payload["user_id"] = str(current_user.id)
    return await HistoryService.add_message(session_id, payload)
