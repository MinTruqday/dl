import hmac
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.redis import redis
from src.repositories.conversation import ConversationRepository
from src.services.thread import ThreadService


password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)

class PasscodeService:
    @staticmethod
    def _attempt_key(user_id: str, participant_key: str) -> str:
        return f"messaging:pin-attempts:{user_id}:{participant_key}"

    @staticmethod
    @log_logic_execution
    async def set_pin_lock(other_user_id: str, pin_code: str, current_user) -> dict:
        user_id = str(current_user.id)
        if len(pin_code) != 4 or not pin_code.isdigit():
            raise HTTPException(status_code=400, detail="Mã PIN ẩn trò chuyện phải gồm đúng 4 chữ số")
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {
                "$set": {
                    f"hidden_pin_hash.{user_id}": password_hasher.hash(pin_code),
                    f"is_hidden.{user_id}": True,
                },
                "$unset": {f"hidden_pin.{user_id}": ""},
            },
            upsert=True,
        )
        return {"status": "hidden", "other_user_id": other_user_id, "has_pin": True}

    @staticmethod
    @log_logic_execution
    async def verify_pin(other_user_id: str, pin_code: str, current_user) -> dict:
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        conv = await ConversationRepository.find_one({"_id": participant_key})
        if not conv:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        client = redis.get_client()
        attempt_key = PasscodeService._attempt_key(user_id, participant_key)
        attempts = int(await client.get(attempt_key) or 0)
        if attempts >= 5:
            raise HTTPException(
                status_code=429,
                detail="Đã vượt quá số lần xác thực mã PIN cho phép",
            )
        hidden_pin_hash = conv.get("hidden_pin_hash", {}).get(user_id)
        legacy_pin = conv.get("hidden_pin", {}).get(user_id)
        valid = False
        if hidden_pin_hash:
            try:
                valid = password_hasher.verify(hidden_pin_hash, pin_code)
            except (InvalidHashError, VerifyMismatchError):
                valid = False
        elif legacy_pin:
            valid = hmac.compare_digest(str(legacy_pin), pin_code)
            if valid:
                await ConversationRepository.update_one(
                    {"_id": participant_key},
                    {
                        "$set": {
                            f"hidden_pin_hash.{user_id}": password_hasher.hash(pin_code)
                        },
                        "$unset": {f"hidden_pin.{user_id}": ""},
                    },
                )
        if not valid:
            attempts = await client.incr(attempt_key)
            if attempts == 1:
                await client.expire(attempt_key, 900)
            raise HTTPException(status_code=401, detail="Mã PIN không chính xác")
        await client.delete(attempt_key)
        return {"status": "unlocked", "other_user_id": other_user_id}

    @staticmethod
    @log_logic_execution
    async def remove_pin_lock(other_user_id: str, pin_code: str, current_user) -> dict:
        user_id = str(current_user.id)
        if other_user_id.startswith("group_"):
            await ThreadService.ensure_group_access(other_user_id, user_id)
        participant_key = (
            other_user_id
            if other_user_id.startswith("group_")
            else f"{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        )
        conv = await ConversationRepository.find_one({"_id": participant_key})
        if not conv:
            raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")
        await PasscodeService.verify_pin(other_user_id, pin_code, current_user)
        await ConversationRepository.update_one(
            {"_id": participant_key},
            {
                "$unset": {
                    f"hidden_pin.{user_id}": "",
                    f"hidden_pin_hash.{user_id}": "",
                },
                "$set": {f"is_hidden.{user_id}": False},
            },
        )
        return {"status": "unhidden", "other_user_id": other_user_id, "has_pin": False}
