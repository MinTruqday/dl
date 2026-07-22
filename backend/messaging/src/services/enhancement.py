import re

from fastapi import HTTPException

from src.core.logic_logger import log_logic_execution
from src.repositories.message import MessageRepository
from src.services.thread import ThreadService

class EnhancementService:
    @staticmethod
    @log_logic_execution
    async def translate_message(
        message_id: str, target_lang: str, current_user, bearer_token: str
    ):
        msg = await MessageRepository.find_one({"_id": message_id})
        user_id = str(current_user.id)
        await ThreadService.ensure_message_access(msg, user_id)
        if not re.fullmatch(r"[A-Za-z-]{2,12}", target_lang):
            raise HTTPException(status_code=400, detail="Mã ngôn ngữ đích không hợp lệ")
        content = msg.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="Tin nhắn không có nội dung để dịch")
        from src.core.http import make_ai_request
        from src.core.infrastructure.configuration import settings

        try:
            response = await make_ai_request(
                f"{settings.AGENTIC_AI_URL}/suy-luan/dich-thuat",
                json_data={"text": content, "target_lang": target_lang},
                bearer_token=bearer_token,
            )
            translated_content = response.json().get("translation")
        except Exception:
            raise HTTPException(status_code=503, detail="Dịch vụ dịch thuật tạm thời không khả dụng")
        if not translated_content:
            raise HTTPException(status_code=502, detail="Dịch vụ dịch thuật trả về dữ liệu không hợp lệ")
        await MessageRepository.update_one(
            {"_id": message_id},
            {"$set": {f"translations.{user_id}.{target_lang.lower()}": translated_content}},
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
        if seconds not in {0, 10, 30, 60, 300, 3600, 86400}:
            raise HTTPException(status_code=400, detail="Thời gian tự hủy không hợp lệ")
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, str(current_user.id))
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
    async def generate_quick_replies(other_user_id: str, current_user, bearer_token: str):
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, str(current_user.id))
            query = {"receiver_id": other_user_id}
        else:
            query = {
                "$or": [
                    {"sender_id": str(current_user.id), "receiver_id": other_user_id},
                    {"sender_id": other_user_id, "receiver_id": str(current_user.id)},
                ]
            }
        query["deleted_by"] = {"$ne": str(current_user.id)}
        query["is_scheduled"] = {"$ne": True}
        query["$and"] = [
            {"$or": [{"visible_to": None}, {"visible_to": str(current_user.id)}]}
        ]
        messages = (
            await MessageRepository
            .find(query)
            .sort("_id", -1)
            .limit(5)
            .to_list(length=5)
        )
        
        if not messages:
            return {"replies": []}

        history_messages = [msg.get("content", "") for msg in reversed(messages) if msg.get("content")]
        if not history_messages:
            return {"replies": []}

        from src.core.http import make_ai_request
        from src.core.infrastructure.configuration import settings
        
        try:
            response = await make_ai_request(
                f"{settings.AGENTIC_AI_URL}/suy-luan/goi-y-tra-loi",
                json_data={"history_messages": history_messages},
                bearer_token=bearer_token,
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            raise HTTPException(status_code=503, detail="Dịch vụ gợi ý trả lời tạm thời không khả dụng")
        raise HTTPException(status_code=502, detail="Dịch vụ gợi ý trả lời trả về dữ liệu không hợp lệ")
