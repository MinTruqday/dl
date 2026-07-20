from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import asyncio
from datetime import datetime, timezone

import httpx
from fastapi import Query
from src.schemas.thread import Record

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.message import MessageRepository
from src.repositories.conversation import ConversationRepository
from src.repositories.message import MessageRepository
from src.repositories.profile import ProfileRepository
from src.repositories.message import MessageRepository

class EnhancementService:
    @staticmethod
    @log_logic_execution
    async def translate_message(
        message_id: str, target_lang: str, current_user
    ):
        msg = await MessageRepository.find_one({"_id": message_id})
        if not msg:
            return None
        from src.core.http import make_ai_request
        from src.core.infrastructure.configuration import settings

        translated_content = ""
        try:
            response = await make_ai_request(
                f"{settings.AGENTIC_AI_URL}/dich-thuat",
                json_data={"text": msg["content"], "target_lang": target_lang},
            )
            if response.status_code == 200:
                translated_content = response.json().get("data")
        except Exception:
            translated_content = f"Translation fallback string for {msg['content']}"
        translations = msg.get("translations", {})
        translations[target_lang] = translated_content
        await MessageRepository.update_one(
            {"_id": message_id}, {"$set": {"translations": translations}}
        )
        return {
            "translated_content": translated_content,
            "target_lang": target_lang,
            "receiver_id": msg["receiver_id"],
            "sender_id": msg["sender_id"],
        }

    @staticmethod
    @log_logic_execution
    async def toggle_self_destruct(
        other_user_id: str, seconds: int, current_user
    ):
        settings_id = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"settings_{min(str(current_user.id), other_user_id)}_{max(str(current_user.id), other_user_id)}"
        )
        await MessageRepository.update_setting(
            {"_id": settings_id},
            {"$set": {"self_destruct_seconds": seconds}},
            upsert=True,
        )
        return {"self_destruct_seconds": seconds}

    @staticmethod
    @log_logic_execution
    async def generate_quick_replies(other_user_id: str, current_user):
        if other_user_id.startswith("group_"):
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": str(current_user.id)},
                ]
            }
        query["deleted_by"] = {"$ne": str(current_user.id)}
        messages = (
            await MessageRepository
            .find(query)
            .sort("_id", -1)
            .limit(5)
            .to_list(length=5)
        )
        
        if not messages:
            return {"replies": ["Chào bạn", "Có chuyện gì thế?", "Tôi có thể giúp gì?"]}
            
        history_messages = [msg.get("content", "") for msg in reversed(messages) if msg.get("content")]
        if not history_messages:
            return {"replies": ["Chào bạn", "Có chuyện gì thế?", "Tôi có thể giúp gì?"]}
            
        from src.core.http import make_ai_request
        from src.core.infrastructure.configuration import settings
        
        try:
            response = await make_ai_request(
                f"{settings.AGENTIC_AI_URL}/goi-y-tra-loi",
                json_data={"history_messages": history_messages},
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            pass
            
        return {"replies": ["Đồng ý", "Cảm ơn", "Tôi hiểu"]}

