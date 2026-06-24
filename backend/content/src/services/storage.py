from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Query
from loguru import logger
from src.schemas.storage import StorageItemCreate, StorageItemInDB, StorageItemUpdate

from shared.infrastructure.configuration import settings
from shared.infrastructure.database import database
from shared.repositories.base_repository import RepositoryFactory


class StorageService:

    @staticmethod
    async def create_item(
        item: StorageItemCreate, owner_id: str, db=None
    ) -> StorageItemInDB:
        db_item = StorageItemInDB(**item.dict(), owner_id=owner_id)
        await database.mongodb.get_default_database().storage_items.insert_one(
            db_item.dict(by_alias=True)
        )
        if db_item.size and db_item.size > 0:
            await database.mongodb.get_default_database().users.update_one(
                {"_id": owner_id}, {"$inc": {"used_storage": db_item.size}}
            )
        return db_item

    @staticmethod
    async def get_storage_quota(owner_id: str, db=None) -> dict:
        user = await database.mongodb.get_default_database().users.find_one(
            {"_id": owner_id}
        )
        limit = (
            user.get("storage_limit", 1 * 1024 * 1024 * 1024)
            if user
            else 1 * 1024 * 1024 * 1024
        )
        used = user.get("used_storage", 0) if user else 0
        return {"used": used, "limit": limit}

    @staticmethod
    async def create_shortcut(
        item_id: str, parent_id: Optional[str], owner_id: str, db=None
    ) -> Optional[StorageItemInDB]:
        target = await StorageService.get_item(item_id)
        if not target:
            return None
        shortcut = StorageItemInDB(
            name=f"Shortcut to {target.name}",
            parent_id=parent_id,
            owner_id=owner_id,
            is_folder=False,
            is_shortcut=True,
            target_id=item_id,
        )
        await database.mongodb.get_default_database().storage_items.insert_one(
            shortcut.dict(by_alias=True)
        )
        return shortcut

    @staticmethod
    async def get_items_by_parent(
        parent_id: Optional[str],
        owner_id: str,
        is_trashed: bool = False,
        is_starred: Optional[bool] = None,
        db=None,
    ) -> List[StorageItemInDB]:
        query = {
            "$or": [{"owner_id": owner_id}, {"shared_with.user_id": owner_id}],
            "parent_id": parent_id,
            "is_trashed": is_trashed,
        }
        if is_starred is not None:
            query["is_starred"] = is_starred
        cursor = (
            database.mongodb.get_default_database()
            .storage_items.find(query)
            .sort([("is_folder", -1), ("name", 1)])
        )
        items = await cursor.to_list(length=1000)
        return [StorageItemInDB(**item) for item in items]

    @staticmethod
    async def search_items(
        query_str: str, owner_id: str, type_filter: Optional[str] = None, db=None
    ) -> List[StorageItemInDB]:
        query = {
            "$or": [{"owner_id": owner_id}, {"shared_with.user_id": owner_id}],
            "is_trashed": False,
            "name": {"$regex": query_str, "$options": "i"},
        }
        if type_filter == "folder":
            query["is_folder"] = True
        elif type_filter == "file":
            query["is_folder"] = False
        cursor = (
            database.mongodb.get_default_database()
            .storage_items.find(query)
            .sort([("created_at", -1)])
        )
        items = await cursor.to_list(length=1000)
        return [StorageItemInDB(**item) for item in items]

    @staticmethod
    async def get_item(
        item_id: str, owner_id: str = None, db=None
    ) -> Optional[StorageItemInDB]:
        query = {"_id": item_id}
        if owner_id:
            query["owner_id"] = owner_id
        item = await database.mongodb.get_default_database().storage_items.find_one(
            query
        )
        if item:
            return StorageItemInDB(**item)
        return None

    @staticmethod
    async def update_item(
        item_id: str, owner_id: str, update_data: StorageItemUpdate, db=None
    ) -> Optional[StorageItemInDB]:
        update_dict = {k: v for (k, v) in update_data.dict(exclude_unset=True).items()}
        if not update_dict:
            return await StorageService.get_item(item_id, owner_id)
        update_dict["updated_at"] = datetime.now(timezone.utc)
        result = await database.mongodb.get_default_database().storage_items.find_one_and_update(
            {"_id": item_id, "owner_id": owner_id},
            {"$set": update_dict},
            return_document=True,
        )
        if result:
            return StorageItemInDB(**result)
        return None

    @staticmethod
    async def delete_item(item_id: str, owner_id: str, db=None) -> bool:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return False

        should_delete_physical = False
        old_version_urls = []
        if not item.is_folder and (not item.is_shortcut) and item.url:
            ref_count = await database.mongodb.get_default_database().storage_items.count_documents(
                {"url": item.url}
            )
            if ref_count <= 1:
                should_delete_physical = True
                if hasattr(item, "versions") and item.versions:
                    old_version_urls = [
                        v.get("url")
                        for v in item.versions
                        if v.get("url") and v.get("url") != item.url
                    ]

        result = (
            await database.mongodb.get_default_database().storage_items.delete_one(
                {"_id": item_id, "owner_id": owner_id}
            )
        )
        if result.deleted_count == 0:
            return False

        if item.size and item.size > 0:
            await database.mongodb.get_default_database().users.update_one(
                {"_id": owner_id}, {"$inc": {"used_storage": -item.size}}
            )

        await database.mongodb.get_default_database().storage_items.delete_many(
            {"target_id": item_id}
        )

        if should_delete_physical:
            from shared.infrastructure.configuration import settings
            from shared.storage import get_storage_client

            try:
                storage_client = await get_storage_client()
                await storage_client.delete_object(
                    Bucket=settings.MINIO_BUCKET_NAME, Key=item.url
                )
                for old_url in old_version_urls:
                    try:
                        await storage_client.delete_object(
                            Bucket=settings.MINIO_BUCKET_NAME, Key=old_url
                        )
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Lỗi dọn dẹp bộ nhớ: {e}")

        return True

    @staticmethod
    async def _copy_children(source_parent_id: str, new_parent_id: str, owner_id: str):
        cursor = database.mongodb.get_default_database().storage_items.find(
            {"owner_id": owner_id, "parent_id": source_parent_id, "is_trashed": False}
        )
        children = await cursor.to_list(length=None)
        for child in children:
            child_dict = StorageItemInDB(**child).dict()
            child_id_old = child_dict.pop("id", None)
            child_dict["parent_id"] = new_parent_id
            new_child = StorageItemInDB(**child_dict)
            await database.mongodb.get_default_database().storage_items.insert_one(
                new_child.dict(by_alias=True)
            )
            if new_child.is_folder:
                await StorageService._copy_children(
                    str(child_id_old), str(new_child.id), owner_id
                )

    @staticmethod
    async def copy_item(
        item_id: str, owner_id: str, target_parent_id: Optional[str] = None, db=None
    ) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return None
        new_item_dict = item.dict()
        new_item_dict["name"] = f"{item.name} (Copy)"
        if target_parent_id is not None:
            new_item_dict["parent_id"] = target_parent_id
        new_item_dict.pop("id", None)
        new_item = StorageItemInDB(**new_item_dict)
        await database.mongodb.get_default_database().storage_items.insert_one(
            new_item.dict(by_alias=True)
        )
        if item.is_folder:
            await StorageService._copy_children(item_id, str(new_item.id), owner_id)
        return new_item

    @staticmethod
    async def add_version(
        item_id: str, owner_id: str, url: str, size: int, db=None
    ) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return None
        from src.schemas.storage import FileVersion

        update_dict = {
            "url": url,
            "size": size,
            "updated_at": datetime.now(timezone.utc),
        }
        update_op = {"$set": update_dict}
        if item.url:
            old_version = FileVersion(
                url=item.url, size=item.size, created_at=item.updated_at
            )
            update_op["$push"] = {
                "versions": {"$each": [old_version.dict()], "$slice": -10}
            }

        size_diff = size - (item.size or 0)
        await database.mongodb.get_default_database().storage_items.update_one(
            {"_id": item_id, "owner_id": owner_id}, update_op
        )
        if size_diff != 0:
            await database.mongodb.get_default_database().users.update_one(
                {"_id": owner_id}, {"$inc": {"used_storage": size_diff}}
            )

        return await StorageService.get_item(item_id, owner_id)

    @staticmethod
    async def get_public_item(share_token: str, db=None) -> Optional[StorageItemInDB]:
        item = await database.mongodb.get_default_database().storage_items.find_one(
            {"share_token": share_token, "is_public": True}
        )
        if item:
            return StorageItemInDB(**item)
        return None

    @staticmethod
    async def share_item(
        item_id: str, email: str, role: str, owner_id: str, db=None
    ) -> dict:
        target_user = await database.mongodb.get_default_database().users.find_one(
            {"email": email}
        )
        if not target_user:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail="Không tìm thấy người dùng với email này"
            )
        target_user_id = str(target_user["_id"])
        if target_user_id == owner_id:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400, detail="Không thể chia sẻ tài liệu với chính mình"
            )
        item = await database.mongodb.get_default_database().storage_items.find_one(
            {"_id": item_id, "owner_id": owner_id}
        )
        if not item:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail="Không tìm thấy tệp hoặc không có quyền chia sẻ"
            )
        result = (
            await database.mongodb.get_default_database().storage_items.update_one(
                {"_id": item_id, "shared_with.user_id": {"$ne": target_user_id}},
                {
                    "$addToSet": {
                        "shared_with": {"user_id": target_user_id, "role": role}
                    }
                },
            )
        )
        if result.modified_count == 0:
            return {"message": "Tệp tin đã được chia sẻ"}
        return {"message": "Chia sẻ tệp thành công"}

    @staticmethod
    async def get_recent_items(
        owner_id: str,
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        ),
        db=None,
    ) -> List[StorageItemInDB]:
        query = {
            "$or": [{"owner_id": owner_id}, {"shared_with.user_id": owner_id}],
            "is_trashed": False,
            "is_folder": False,
        }
        cursor = (
            database.mongodb.get_default_database()
            .storage_items.find(query)
            .sort([("updated_at", -1)])
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        return [StorageItemInDB(**item) for item in items]
