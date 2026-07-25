import re
import secrets
from datetime import datetime, timezone

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
            translated_content = f"[Dịch tự động {target_lang}]: {content}"
        if not translated_content:
            translated_content = f"[Dịch tự động {target_lang}]: {content}"

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
            pass
        return {"replies": ["Đã rõ thông tin", "Tôi sẽ xem xét và phản hồi sau", "Cảm ơn bạn"]}


    @staticmethod
    @log_logic_execution
    async def generate_group_invite(group_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        await ThreadService.ensure_group_access(group_id, user_id)
        invite_code = f"inv_{secrets.token_hex(6)}"
        from src.core.infrastructure.mongo import mongo
        await mongo.update_one(
            "message_groups",
            {"_id": group_id},
            {"$set": {"invite_code": invite_code, "invite_created_at": datetime.now(timezone.utc)}},
        )
        return {
            "status": "success",
            "group_id": group_id,
            "invite_code": invite_code,
            "invite_url": f"/tin-nhan/nhom/tham-gia/{invite_code}",
        }

    @staticmethod
    @log_logic_execution
    async def join_by_invite(invite_code: str, current_user) -> dict:
        user_id = str(current_user.id)
        group = await MessageRepository.find_group({"invite_code": invite_code})
        if not group:
            raise HTTPException(status_code=404, detail="Mã mời nhóm không tồn tại hoặc đã hết hạn")
        group_id = str(group["_id"])
        from src.core.infrastructure.mongo import mongo
        await mongo.update_one(
            "message_groups",
            {"_id": group_id},
            {"$addToSet": {"members": user_id, "participants": user_id}},
        )
        return {
            "status": "success",
            "group_id": group_id,
            "group_name": group.get("name", "Nhóm trò chuyện"),
        }


    @staticmethod
    @log_logic_execution
    async def set_nickname(other_user_id: str, nickname: str, current_user) -> dict:
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await MessageRepository.update_one(
            {"_id": participant_key},
            {"$set": {f"nicknames.{other_user_id}": nickname.strip()}},
            upsert=True,
        )
        return {"nickname": nickname.strip(), "target_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def share_contact_card(other_user_id: str, contact_user_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        from src.repositories.profile import ProfileRepository

        contact_profile = await ProfileRepository.get_profile(contact_user_id)
        if not contact_profile:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh thiếp người dùng")

        card_attachment = {
            "type": "contact_card",
            "user_id": contact_user_id,
            "full_name": contact_profile.get("full_name", "Người dùng DocLib"),
            "email": contact_profile.get("email", ""),
            "avatar": contact_profile.get("avatar_url", ""),
        }

        msg_doc = {
            "sender_id": user_id,
            "receiver_id": other_user_id,
            "content": f"Đã chia sẻ danh thiếp của {contact_profile.get('full_name', 'Người dùng DocLib')}",
            "attachments": [card_attachment],
            "created_at": datetime.now(timezone.utc),
        }
        inserted = await MessageRepository.insert_one(msg_doc)
        return {
            "status": "success",
            "message_id": str(inserted.inserted_id),
            "contact_card": card_attachment,
        }

    @staticmethod
    @log_logic_execution
    async def archive_thread(other_user_id: str, is_archived: bool, current_user) -> dict:
        user_id = str(current_user.id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        if is_archived:
            await MessageRepository.update_one(
                {"_id": participant_key},
                {"$addToSet": {"archived_by": user_id}},
                upsert=True,
            )
        else:
            await MessageRepository.update_one(
                {"_id": participant_key},
                {"$pull": {"archived_by": user_id}},
            )
        return {"is_archived": is_archived, "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def set_auto_reply(auto_reply_text: str, is_enabled: bool, current_user) -> dict:
        user_id = str(current_user.id)
        await MessageRepository.update_setting(
            {"_id": f"auto_reply_{user_id}"},
            {
                "$set": {
                    "user_id": user_id,
                    "text": auto_reply_text.strip(),
                    "is_enabled": is_enabled,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        return {"is_enabled": is_enabled, "auto_reply_text": auto_reply_text.strip()}

    @staticmethod
    @log_logic_execution
    async def manage_group_permissions(group_id: str, admin_only: bool, current_user) -> dict:
        user_id = str(current_user.id)
        from src.core.infrastructure.mongo import mongo

        group = await MessageRepository.find_group({"_id": group_id})
        if not group or group.get("created_by") != user_id:
            raise HTTPException(status_code=403, detail="Chỉ Trưởng nhóm mới có quyền thay đổi quyền gửi tin nhắn")
        await mongo.update_one(
            "message_groups",
            {"_id": group_id},
            {"$set": {"messaging_restricted": admin_only}},
        )
        return {"status": "success", "group_id": group_id, "admin_only": admin_only}

    @staticmethod
    @log_logic_execution
    async def create_group_event(group_id: str, title: str, event_time: str, current_user) -> dict:
        user_id = str(current_user.id)
        await ThreadService.ensure_group_access(group_id, user_id)
        from src.core.infrastructure.mongo import mongo

        event_doc = {
            "group_id": group_id,
            "title": title.strip(),
            "event_time": event_time,
            "created_by": user_id,
            "created_at": datetime.now(timezone.utc),
        }
        await mongo.update_one(
            "message_groups",
            {"_id": group_id},
            {"$set": {"active_event": event_doc}},
        )
        return {"status": "success", "event": event_doc}

    @staticmethod
    @log_logic_execution
    async def set_vip_priority(other_user_id: str, is_vip: bool, current_user) -> dict:
        user_id = str(current_user.id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        if is_vip:
            await MessageRepository.update_one(
                {"_id": participant_key},
                {"$addToSet": {"vip_by": user_id}},
                upsert=True,
            )
        else:
            await MessageRepository.update_one(
                {"_id": participant_key},
                {"$pull": {"vip_by": user_id}},
            )
        return {"is_vip": is_vip, "other_user_id": other_user_id}


