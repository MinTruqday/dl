from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.repositories.conversation import ConversationRepository

class PasscodeService:
    @staticmethod
    @log_logic_execution
    async def set_pin_lock(other_user_id: str, pin_code: str, current_user) -> dict:
        user_id = str(current_user.id)
        if len(pin_code) != 4 or not pin_code.isdigit():
            raise HTTPException(status_code=400, detail="Mã PIN ẩn trò chuyện phải gồm đúng 4 chữ số")
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {
                "$set": {
                    f"hidden_pin.{user_id}": pin_code,
                    f"is_hidden.{user_id}": True,
                }
            },
            upsert=True,
        )
        return {"status": "hidden", "other_user_id": other_user_id, "has_pin": True}

    @staticmethod
    @log_logic_execution
    async def verify_pin(other_user_id: str, pin_code: str, current_user) -> dict:
        user_id = str(current_user.id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        conv = await ConversationRepository.find_one({"_id": participant_key})
        if not conv:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        hidden_pin = conv.get("hidden_pin", {}).get(user_id)
        if not hidden_pin or hidden_pin != pin_code:
            raise HTTPException(status_code=401, detail="Mã PIN không chính xác")
        return {"status": "unlocked", "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def remove_pin_lock(other_user_id: str, pin_code: str, current_user) -> dict:
        user_id = str(current_user.id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        conv = await ConversationRepository.find_one({"_id": participant_key})
        if not conv:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        hidden_pin = conv.get("hidden_pin", {}).get(user_id)
        if hidden_pin and hidden_pin != pin_code:
            raise HTTPException(status_code=401, detail="Mã PIN không chính xác")
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {
                "$unset": {f"hidden_pin.{user_id}": ""},
                "$set": {f"is_hidden.{user_id}": False},
            },
        )
        return {"status": "unhidden", "other_user_id": other_user_id, "has_pin": False}
