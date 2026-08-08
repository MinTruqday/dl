from datetime import datetime, timezone, timedelta
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
        lock = await CooperationRepository.find_lock({"document_id": document_id})
        now = datetime.now(timezone.utc)
        if lock:
            locked_at = lock.get("locked_at")
            if isinstance(locked_at, datetime) and locked_at.tzinfo is None:
                locked_at = locked_at.replace(tzinfo=timezone.utc)
            if (
                lock["locked_by"] != str(current_user.id)
                and locked_at
                and locked_at > now - timedelta(minutes=5)
            ):
                raise HTTPException(
                    status_code=423,
                    detail=f"Tài liệu hiện đang được chỉnh sửa độc quyền bởi {lock.get('user_name', 'người dùng khác')}",
                )
        await CooperationRepository.update_lock(
            {"document_id": document_id},
            {
                "$set": {
                    "document_id": document_id,
                    "locked_by": str(current_user.id),
                    "user_name": current_user.full_name,
                    "locked_at": now,
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
        lock = await CooperationRepository.find_lock({"document_id": document_id})
        if not lock:
            return {"message": "Tài liệu hiện không bị khóa"}
        if lock["locked_by"] != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="Bạn không phải người đang nắm giữ khóa tài liệu này"
            )
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
        lock = await CooperationRepository.find_lock({"document_id": document_id})
        if not lock:
            return {"is_locked": False}
        now = datetime.now(timezone.utc)
        locked_at = lock.get("locked_at")
        if isinstance(locked_at, datetime) and locked_at.tzinfo is None:
            locked_at = locked_at.replace(tzinfo=timezone.utc)
        if locked_at and locked_at < now - timedelta(minutes=5):
            return {"is_locked": False}
        return {
            "is_locked": True,
            "locked_by": lock["locked_by"],
            "user_name": lock.get("user_name"),
            "locked_at": locked_at.isoformat() if locked_at else None,
        }
