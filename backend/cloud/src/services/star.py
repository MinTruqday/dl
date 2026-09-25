from fastapi import HTTPException

from src.repositories.storage import storage_repository


class StarService:
    @staticmethod
    async def toggle_star_item(item_id: str, owner_id: str) -> dict:
        item = await storage_repository.find_one(
            {"_id": item_id, "owner_id": owner_id}
        )
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy mục cần gắn sao")
        new_starred = not item.get("is_starred", False)
        await storage_repository.update_one(
            {"_id": item_id}, {"$set": {"is_starred": new_starred}}
        )
        return {"item_id": item_id, "is_starred": new_starred}

    @staticmethod
    async def get_starred_items(owner_id: str) -> list:
        return await storage_repository.find_many(
            {"owner_id": owner_id, "is_starred": True, "is_trashed": False},
            limit=100,
        )
