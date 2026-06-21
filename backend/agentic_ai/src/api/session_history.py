import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from uuid6 import uuid7

from core.config import settings
from src.services.history import HistoryService

router = APIRouter(prefix="/lich-su")


def get_db():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client.get_default_database()
    try:
        yield db
    finally:
        client.close()


@router.post("", response_model=Dict[str, Any])
async def create_session(data: dict):
    return await HistoryService.create_session(data)


@router.get("", response_model=List[dict])
async def get_user_sessions(
    user_id: str, document_id: Optional[str] = None
):
    return await HistoryService.get_user_sessions(user_id, document_id)


@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_detail(session_id: str, user_id: str):
    return await HistoryService.get_session_detail(session_id, user_id)


@router.put("/{session_id}/tieu-de", response_model=Dict[str, Any])
async def update_title(session_id: str, data: dict, user_id: str):
    return await HistoryService.update_title(session_id, data, user_id)


@router.delete("/{session_id}", response_model=Dict[str, Any])
async def delete_session(session_id: str, user_id: str):
    return await HistoryService.delete_session(session_id, user_id)


@router.post("/{session_id}/tin-nhan", response_model=Dict[str, Any])
async def add_message(session_id: str, data: dict):
    return await HistoryService.add_message(session_id, data)
