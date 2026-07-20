from src.core.infrastructure.redis import redis
import json
from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query
from src.schemas.thread import Conversation, Creation, Response
from src.services.conversation import ConversationService

from src.core.infrastructure.database import database
from src.core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from src.core.dependency import get_current_user
from src.core.response import APIResponse
from src.repositories.message import MessageRepository

from src.api.thread import publish_personal_message
router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.get("/cuoc-tro-chuyen", response_model=APIResponse[Any])
async def get_conversations(current_user=Depends(get_current_user)):
    return APIResponse(
        data=await ConversationService.get_conversations(current_user),
        message="Trích xuất danh sách cuộc trò chuyện hoàn tất",
        status=200,
    )

@router.post("/{other_user_id}/doc-hieu", response_model=APIResponse[Any])
async def mark_as_read(other_user_id: str, current_user=Depends(get_current_user)):
    result = await ConversationService.mark_as_read(other_user_id, current_user)
    await publish_personal_message(
        {"type": "messages_read", "data": {"viewer_id": current_user.id}}, other_user_id
    )
    return APIResponse(data=result, message="Đã đánh dấu cuộc trò chuyện là đã đọc")

@router.post("/{other_user_id}/ban-nhap", response_model=APIResponse[Any])
async def save_draft(
    other_user_id: str, req: dict, current_user=Depends(get_current_user)
):
    content = req.get("content", "")
    result = await ConversationService.save_draft(other_user_id, content, current_user)
    return APIResponse(data=result, message="Lưu bản nháp tin nhắn hoàn tất")

@router.get("/{other_user_id}/ban-nhap", response_model=APIResponse[Any])
async def get_draft(other_user_id: str, current_user=Depends(get_current_user)):
    result = await ConversationService.get_draft(other_user_id, current_user)
    return APIResponse(data=result, message="Trích xuất bản nháp tin nhắn hoàn tất")

@router.get("/{other_user_id}/cai-dat", response_model=APIResponse[Any])
async def get_conversation_settings(
    other_user_id: str, current_user=Depends(get_current_user)
):
    result = await ConversationService.get_conversation_settings(other_user_id, current_user)
    is_online = False
    result["is_online"] = is_online
    return APIResponse(data=result, message="Trích xuất cấu hình cuộc trò chuyện hoàn tất")

@router.put("/{other_user_id}/cai-dat", response_model=APIResponse[Any])
async def update_conversation_settings(
    other_user_id: str, req: dict, current_user=Depends(get_current_user)
):
    result = await ConversationService.update_conversation_settings(other_user_id, req, current_user)
    return APIResponse(data=result, message="Cập nhật cấu hình cuộc trò chuyện hoàn tất")

@router.delete("/cuoc-tro-chuyen/{other_user_id}", response_model=APIResponse[Any])
async def delete_conversation(
    other_user_id: str, current_user=Depends(get_current_user)
):
    result = await ConversationService.delete_conversation(other_user_id, current_user)
    return APIResponse(data=result, message="Xóa lịch sử cuộc trò chuyện hoàn tất")
