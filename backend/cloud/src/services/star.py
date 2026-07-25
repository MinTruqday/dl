from fastapi import HTTPException
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.logic_logger import log_logic_execution

class StarService:
    @staticmethod
    @log_logic_execution
    async def toggle_star_item(item_id: str, owner_id: str) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({"_id": item_id, "owner_id": owner_id})
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy mục cần gắn sao")
        new_starred = not item.get("is_starred", False)
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": item_id},
            {"$set": {"is_starred": new_starred}}
        )
        return {"item_id": item_id, "is_starred": new_starred}

    @staticmethod
    @log_logic_execution
    async def get_starred_items(owner_id: str) -> list:
        cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_items.find({"owner_id": owner_id, "is_starred": True, "is_trashed": False})
        return await cursor.to_list(length=100)
