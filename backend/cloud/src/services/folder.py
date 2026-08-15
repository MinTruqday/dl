from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.schemas.storage import StorageItemCreate, StorageItemInDB

class FolderService:
    @staticmethod
    async def create_folder(name: str, parent_id: Optional[str], owner_id: str) -> StorageItemInDB:
        if parent_id:
            parent = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
                {"_id": parent_id, "owner_id": owner_id, "is_folder": True, "is_trashed": {"$ne": True}}
            )
            if not parent:
                raise HTTPException(status_code=400, detail="Thư mục cha không hợp lệ")

        folder_item = StorageItemInDB(
            name=name,
            is_folder=True,
            parent_id=parent_id,
            owner_id=owner_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.insert_one(
            folder_item.model_dump(by_alias=True)
        )
        return folder_item

    @staticmethod
    async def get_folder_contents(folder_id: Optional[str], owner_id: str) -> List[dict]:
        query = {
            "owner_id": owner_id,
            "parent_id": folder_id,
            "is_trashed": {"$ne": True},
        }
        cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(query).sort("name", 1)
        items = await cursor.to_list(length=500)
        return items

    @staticmethod
    async def get_folder_tree(owner_id: str) -> List[dict]:
        query = {
            "owner_id": owner_id,
            "is_folder": True,
            "is_trashed": {"$ne": True},
        }
        cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(query).sort("name", 1)
        folders = await cursor.to_list(length=1000)
        return folders

    @staticmethod
    async def rename_folder(folder_id: str, new_name: str, owner_id: str) -> dict:
        res = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": folder_id, "owner_id": owner_id, "is_folder": True},
            {"$set": {"name": new_name, "updated_at": datetime.now(timezone.utc)}},
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
        return {"status": "success", "folder_id": folder_id, "name": new_name}

    @staticmethod
    async def move_folder(folder_id: str, new_parent_id: Optional[str], owner_id: str) -> dict:
        if new_parent_id == folder_id:
            raise HTTPException(status_code=400, detail="Không thể di chuyển thư mục vào chính nó")
        if new_parent_id:
            parent = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
                {"_id": new_parent_id, "owner_id": owner_id, "is_folder": True, "is_trashed": {"$ne": True}}
            )
            if not parent:
                raise HTTPException(status_code=400, detail="Thư mục đích không tồn tại")
            ancestor = parent
            while ancestor.get("parent_id"):
                if ancestor["parent_id"] == folder_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Không thể di chuyển thư mục vào thư mục con của nó",
                    )
                ancestor = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
                    {
                        "_id": ancestor["parent_id"],
                        "owner_id": owner_id,
                        "is_folder": True,
                    }
                )
                if not ancestor:
                    raise HTTPException(status_code=400, detail="Cây thư mục không hợp lệ")
        res = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": folder_id, "owner_id": owner_id, "is_folder": True},
            {"$set": {"parent_id": new_parent_id, "updated_at": datetime.now(timezone.utc)}},
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
        return {"status": "success", "folder_id": folder_id, "parent_id": new_parent_id}
