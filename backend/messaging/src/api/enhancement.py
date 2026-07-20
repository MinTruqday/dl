from src.core.infrastructure.redis import redis
import json
from typing import Any, List

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query
from src.schemas.thread import Conversation, Creation, Response
from src.services.enhancement import EnhancementService

from src.core.infrastructure.database import database
from src.core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from src.core.dependency import get_current_user
from src.core.response import APIResponse
from src.repositories.message import MessageRepository

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.post("/{message_id}/dich-thuat", response_model=APIResponse[Any])
async def translate_message(
    message_id: str, req: dict, current_user=Depends(get_current_user)
):
    target_lang = req.get("target_lang", "vi")
    result = await EnhancementService.translate_message(
        message_id, target_lang, current_user
    )
    if not result:
        return APIResponse(message="Không tìm thấy tin nhắn cần dịch", status=404)
    other_id = result.get("receiver_id")
    if other_id:
        await publish_personal_message(
            {
                "type": "message_translated",
                "data": {**result, "message_id": message_id},
            },
            other_id,
        )
    return APIResponse(data=result, message="Dịch văn bản hoàn tất")

@router.post("/{other_user_id}/tu-huy", response_model=APIResponse[Any])
async def toggle_self_destruct(
    other_user_id: str, req: dict, current_user=Depends(get_current_user)
):
    seconds = req.get("seconds", 0)
    result = await EnhancementService.toggle_self_destruct(
        other_user_id, seconds, current_user
    )
    await publish_personal_message(
        {
            "type": "conversation_settings_updated",
            "data": {"self_destruct_seconds": seconds},
        },
        other_user_id,
    )
    return APIResponse(data=result, message="Kích hoạt tính năng tự động hủy tin nhắn hoàn tất")

@router.get("/{other_user_id}/goi-y-tra-loi", response_model=APIResponse[Any])
async def get_quick_replies(
    other_user_id: str, current_user=Depends(get_current_user)
):
    if current_user.role.value != "admin" and (not current_user.ai_tier or current_user.ai_tier.value not in ["PRO", "PREMIUM"]):
        return APIResponse(
            data={"replies": []},
            message="Tính năng Gợi ý trả lời thông minh chỉ dành cho người dùng gói Chuyên sâu hoặc Toàn năng",
            status=403
        )
    
    # Try to get from redis cache
    cache_key = f"quick_replies:{current_user.id}:{other_user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return APIResponse(data=json.loads(cached), message="Trích xuất gợi ý trả lời hoàn tất")
        
    result = await EnhancementService.generate_quick_replies(other_user_id, current_user)
    
    # Cache for 10 seconds to avoid spamming AI
    await redis.set(cache_key, json.dumps(result), ex=10)
    
    return APIResponse(data=result, message="Khởi tạo gợi ý trả lời hoàn tất")

