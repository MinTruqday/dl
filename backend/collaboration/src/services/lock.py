from datetime import datetime, timezone
from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.repositories.cooperation import CooperationRepository, DocumentRepository
from src.services.activity import ActivityService

class LockService:
    @staticmethod
    @log_logic_execution
    async def acquire_lock(document_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        existing = await CooperationRepository.find_lock({"document_id": document_id})
        if existing:
            locked_at = existing.get("locked_at")
            locked_at_timestamp = locked_at.timestamp() if isinstance(locked_at, datetime) else 0
            if locked_at_timestamp > cutoff and existing.get("user_id") != str(current_user.id):
                raise HTTPException(
                    status_code=400,
                    detail="Tài liệu hiện đang trong phiên chỉnh sửa độc quyền của người dùng khác",
                )
        await CooperationRepository.update_lock(
            {"document_id": document_id},
            {
                "$set": {
                    "user_id": str(current_user.id),
                    "user_name": current_user.full_name,
                    "locked_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Acquire lock",
            "Exclusive document edit lock acquired",
        )
        return {"message": "Nhận khóa quyền chỉnh sửa độc quyền thành công"}

    @staticmethod
    @log_logic_execution
    async def release_lock(document_id: str, current_user) -> dict:
        existing = await CooperationRepository.find_lock({"document_id": document_id})
        if existing and existing.get("user_id") == str(current_user.id):
            await CooperationRepository.delete_lock({"document_id": document_id})
            await ActivityService.log_activity(
                document_id,
                current_user.full_name,
                "Release lock",
                "Document edit lock released",
            )
        return {"message": "Mở khóa tài liệu thành công"}

    @staticmethod
    @log_logic_execution
    async def get_lock_status(document_id: str) -> dict:
        existing = await CooperationRepository.find_lock({"document_id": document_id})
        if not existing:
            return {"is_locked": False}
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        locked_at = existing.get("locked_at")
        locked_at_timestamp = locked_at.timestamp() if isinstance(locked_at, datetime) else 0
        return {
            "is_locked": locked_at_timestamp > cutoff,
            "user_id": existing.get("user_id"),
            "user_name": existing.get("user_name"),
            "locked_at": locked_at,
        }
