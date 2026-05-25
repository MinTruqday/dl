from core.database import db_client
from models.storage import StorageItemInDB, StorageItemCreate, StorageItemUpdate
from typing import List, Optional
from datetime import datetime, timezone

class StorageService:
    @staticmethod
    async def create_item(item: StorageItemCreate, owner_id: str) -> StorageItemInDB:
        db_item = StorageItemInDB(
            **item.dict(),
            owner_id=owner_id
        )
        await db_client.mongodb.get_default_database().storage_items.insert_one(db_item.dict(by_alias=True))
        return db_item

    @staticmethod
    async def get_storage_quota(owner_id: str) -> dict:
        user = await db_client.mongodb.get_default_database().users.find_one({"_id": owner_id})
        limit = user.get("storage_limit", 1 * 1024 * 1024 * 1024) if user else 1 * 1024 * 1024 * 1024
        
        pipeline = [
            {"$match": {"owner_id": owner_id, "is_trashed": False, "is_folder": False}},
            {"$group": {"_id": None, "total": {"$sum": "$size"}}}
        ]
        cursor = db_client.mongodb.get_default_database().storage_items.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        used = result[0]["total"] if result else 0
        return {"used": used, "limit": limit}

    @staticmethod
    async def create_shortcut(item_id: str, parent_id: Optional[str], owner_id: str) -> Optional[StorageItemInDB]:
        target = await StorageService.get_item(item_id)
        if not target:
            return None
            
        shortcut = StorageItemInDB(
            name=f"Lối tắt của {target.name}",
            parent_id=parent_id,
            owner_id=owner_id,
            is_folder=False,
            is_shortcut=True,
            target_id=item_id
        )
        await db_client.mongodb.get_default_database().storage_items.insert_one(shortcut.dict(by_alias=True))
        return shortcut

    @staticmethod
    async def get_items_by_parent(parent_id: Optional[str], owner_id: str, is_trashed: bool = False, is_starred: Optional[bool] = None) -> List[StorageItemInDB]:
        query = {
            "$or": [
                {"owner_id": owner_id},
                {"shared_with.user_id": owner_id}
            ],
            "parent_id": parent_id,
            "is_trashed": is_trashed
        }
        if is_starred is not None:
            query["is_starred"] = is_starred
            
        cursor = db_client.mongodb.get_default_database().storage_items.find(query).sort([("is_folder", -1), ("name", 1)])
        items = await cursor.to_list(length=1000)
        return [StorageItemInDB(**item) for item in items]

    @staticmethod
    async def search_items(query_str: str, owner_id: str, type_filter: Optional[str] = None) -> List[StorageItemInDB]:
        query = {
            "$or": [
                {"owner_id": owner_id},
                {"shared_with.user_id": owner_id}
            ],
            "is_trashed": False,
            "name": {"$regex": query_str, "$options": "i"}
        }
        if type_filter == "folder":
            query["is_folder"] = True
        elif type_filter == "file":
            query["is_folder"] = False
            
        cursor = db_client.mongodb.get_default_database().storage_items.find(query).sort([("created_at", -1)])
        items = await cursor.to_list(length=1000)
        return [StorageItemInDB(**item) for item in items]

    @staticmethod
    async def get_item(item_id: str, owner_id: str = None) -> Optional[StorageItemInDB]:
        query = {"_id": item_id}
        if owner_id:
            query["owner_id"] = owner_id
        item = await db_client.mongodb.get_default_database().storage_items.find_one(query)
        if item:
            return StorageItemInDB(**item)
        return None

    @staticmethod
    async def update_item(item_id: str, owner_id: str, update_data: StorageItemUpdate) -> Optional[StorageItemInDB]:
        update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items()}
        if not update_dict:
            return await StorageService.get_item(item_id, owner_id)
            
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await db_client.mongodb.get_default_database().storage_items.find_one_and_update(
            {"_id": item_id, "owner_id": owner_id},
            {"$set": update_dict},
            return_document=True
        )
        if result:
            return StorageItemInDB(**result)
        return None

    @staticmethod
    async def delete_item(item_id: str, owner_id: str) -> bool:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return False
            
        if not item.is_folder and not item.is_shortcut and item.url:
            from core.storage import get_storage_client
            from core.config import settings
            try:
                async with await get_storage_client() as client:
                    await client.delete_object(Bucket=settings.MINIO_BUCKET_NAME, Key=item.url)
            except Exception as e:
                print(f"Error physically deleting file from MinIO: {e}")

        result = await db_client.mongodb.get_default_database().storage_items.delete_one({"_id": item_id, "owner_id": owner_id})
        return result.deleted_count > 0

    @staticmethod
    async def copy_item(item_id: str, owner_id: str, target_parent_id: Optional[str] = None) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return None
        new_item_dict = item.dict()
        new_item_dict["name"] = f"{item.name} (Bản sao)"
        if target_parent_id is not None:
            new_item_dict["parent_id"] = target_parent_id
            
        del new_item_dict["id"]
        new_item = StorageItemInDB(**new_item_dict)
        await db_client.mongodb.get_default_database().storage_items.insert_one(new_item.dict(by_alias=True))
        return new_item

    @staticmethod
    async def add_version(item_id: str, owner_id: str, url: str, size: int) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return None
        
        from models.storage import FileVersion
        
        update_dict = {
            "url": url,
            "size": size,
            "updated_at": datetime.now(timezone.utc)
        }
        
        update_op = {"$set": update_dict}
        
        if item.url:
            old_version = FileVersion(url=item.url, size=item.size, created_at=item.updated_at)
            update_op["$push"] = {"versions": old_version.dict()}
            
        await db_client.mongodb.get_default_database().storage_items.update_one(
            {"_id": item_id, "owner_id": owner_id},
            update_op
        )
        
        return await StorageService.get_item(item_id, owner_id)

    @staticmethod
    async def get_public_item(share_token: str) -> Optional[StorageItemInDB]:
        item = await db_client.mongodb.get_default_database().storage_items.find_one({"share_token": share_token, "is_public": True})
        if item:
            return StorageItemInDB(**item)
        return None

    @staticmethod
    async def share_item(item_id: str, email: str, role: str, owner_id: str) -> dict:
        target_user = await db_client.mongodb.get_default_database().users.find_one({"email": email})
        if not target_user:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản người dùng với email đã nhập.")
        
        target_user_id = str(target_user["_id"])
        if target_user_id == owner_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Bạn không thể chia sẻ tệp tin cho chính mình.")
            
        item = await db_client.mongodb.get_default_database().storage_items.find_one({"_id": item_id, "owner_id": owner_id})
        if not item:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại hoặc bạn không có quyền chia sẻ.")
            
        shared_list = item.get("shared_with", [])
        if any(isinstance(s, dict) and s.get("user_id") == target_user_id for s in shared_list):
            return {"message": "Tệp tin đã được chia sẻ cho người dùng này trước đó."}
            
        await db_client.mongodb.get_default_database().storage_items.update_one(
            {"_id": item_id},
            {"$push": {"shared_with": {"user_id": target_user_id, "role": role}}}
        )
        return {"message": f"Chia sẻ tệp tin thành công tới {email} với quyền {role}."}

    @staticmethod
    async def get_recent_items(owner_id: str, limit: int = 20) -> List[StorageItemInDB]:
        query = {
            "$or": [
                {"owner_id": owner_id},
                {"shared_with.user_id": owner_id}
            ],
            "is_trashed": False,
            "is_folder": False
        }
        cursor = db_client.mongodb.get_default_database().storage_items.find(query).sort([("updated_at", -1)]).limit(limit)
        items = await cursor.to_list(length=limit)
        return [StorageItemInDB(**item) for item in items]
