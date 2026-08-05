from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.logic_logger import log_logic_execution

class TrashService:
    @staticmethod
    @log_logic_execution
    async def move_to_trash(item_id: str, owner_id: str) -> dict:
        result = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": item_id, "owner_id": owner_id},
            {"$set": {"is_trashed": True, "trashed_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy mục cần chuyển vào Thùng rác")
        return {"status": "success", "message": "Đã chuyển tệp/thư mục vào Thùng rác"}

    @staticmethod
    @log_logic_execution
    async def restore_from_trash(item_id: str, owner_id: str) -> dict:
        result = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": item_id, "owner_id": owner_id, "is_trashed": True},
            {"$set": {"is_trashed": False, "trashed_at": None}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy mục trong Thùng rác")
        return {"status": "success", "message": "Đã khôi phục tệp/thư mục từ Thùng rác"}

    @staticmethod
    @log_logic_execution
    async def empty_trash(owner_id: str) -> dict:
        res = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.delete_many({"owner_id": owner_id, "is_trashed": True})
        return {"status": "success", "deleted_count": res.deleted_count, "message": "Đã dọn sạch Thùng rác"}

    @staticmethod
    @log_logic_execution
    async def auto_purge_expired_trash(owner_id: str, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = {
            "owner_id": owner_id,
            "is_trashed": True,
            "$or": [
                {"trashed_at": {"$lte": cutoff}},
                {"trashed_at": None, "updated_at": {"$lte": cutoff}}
            ]
        }
        res = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.delete_many(query)
        return {
            "status": "success",
            "purged_count": res.deleted_count,
            "days_threshold": days,
            "message": f"Đã tự động dọn {res.deleted_count} mục trong Thùng rác đã quá hạn {days} ngày"
        }

