from src.core.logic_logger import log_logic_execution
from backend.cloud.src.services.user import UserDirectory
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, Query
from loguru import logger
from src.schemas.storage import StorageItemCreate, StorageItemInDB, StorageItemUpdate

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database

class StorageService:

    @staticmethod
    @log_logic_execution
    async def create_item(
        item: StorageItemCreate, owner_id: str
    ) -> StorageItemInDB:
        if item.parent_id:
            parent = await StorageService.get_item(item.parent_id, owner_id)
            if not parent or not parent.is_folder or parent.is_trashed:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Thư mục cha không hợp lệ")
        if not item.is_folder:
            allowed_prefixes = (f"users/{owner_id}/", f"client/{owner_id}/")
            if not item.url or not item.url.startswith(allowed_prefixes):
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Đường dẫn tệp không thuộc chủ sở hữu")
            existing = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
                {"owner_id": owner_id, "url": item.url}, {"_id": 1}
            )
            if existing:
                from fastapi import HTTPException
                raise HTTPException(status_code=409, detail="Tệp đã được đăng ký trong kho lưu trữ")
            from src.core.storage import get_bucket, get_storage_client
            try:
                client = await get_storage_client()
                metadata = await client.head_object(Bucket=get_bucket(item.url), Key=item.url)
            except Exception:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Không tìm thấy dữ liệu tệp trong kho đối tượng")
            if metadata.get("ContentLength") != item.size:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Kích thước tệp không khớp dữ liệu lưu trữ")
        db_item = StorageItemInDB(**item.model_dump(), owner_id=owner_id)
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.insert_one(
            db_item.model_dump(by_alias=True)
        )
        return db_item

    @staticmethod
    @log_logic_execution
    async def get_storage_quota(owner_id: str) -> dict:
        user = await UserDirectory.get_by_id(owner_id)
        limit = (
            user.get("storage_limit", 1 * 1024 * 1024 * 1024)
            if user
            else 1 * 1024 * 1024 * 1024
        )
        
        pipeline = [
            {"$match": {"owner_id": owner_id, "is_folder": False, "is_shortcut": False}},
            {
                "$project": {
                    "assets": {
                        "$concatArrays": [
                            {
                                "$cond": [
                                    {"$eq": [{"$type": "$url"}, "string"]},
                                    [{"url": "$url", "size": "$size"}],
                                    [],
                                ]
                            },
                            {
                                "$map": {
                                    "input": {"$ifNull": ["$versions", []]},
                                    "as": "version",
                                    "in": {
                                        "url": "$$version.url",
                                        "size": "$$version.size",
                                    },
                                }
                            },
                        ]
                    }
                }
            },
            {"$unwind": "$assets"},
            {
                "$group": {
                    "_id": "$assets.url",
                    "size": {"$max": "$assets.size"},
                }
            },
            {"$group": {"_id": None, "total_used": {"$sum": "$size"}}},
        ]
        result = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.aggregate(pipeline).to_list(1)
        used = (result[0].get("total_used") or 0) if result else 0
        return {"used": used, "limit": limit}

    @staticmethod
    @log_logic_execution
    async def create_shortcut(
        item_id: str, parent_id: Optional[str], owner_id: str
    ) -> Optional[StorageItemInDB]:
        target = await StorageService.get_accessible_item(item_id, owner_id)
        if not target:
            return None
        if parent_id:
            parent = await StorageService.get_item(parent_id, owner_id)
            if not parent or not parent.is_folder:
                return None
        shortcut = StorageItemInDB(
            name=f"Shortcut to {target.name}",
            parent_id=parent_id,
            owner_id=owner_id,
            is_folder=False,
            is_shortcut=True,
            target_id=item_id,
        )
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.insert_one(
            shortcut.model_dump(by_alias=True)
        )
        return shortcut

    @staticmethod
    @log_logic_execution
    async def get_items_by_parent(
        parent_id: Optional[str],
        owner_id: str,
        is_trashed: bool = False,
        is_starred: Optional[bool] = None,
    ) -> List[StorageItemInDB]:
        access_query = {"$or": [{"owner_id": owner_id}, {"shared_with.user_id": owner_id}]}
        if parent_id:
            parent = await StorageService.get_accessible_item(parent_id, owner_id)
            if not parent:
                return []
            access_query = {"owner_id": parent.owner_id}
        query = {**access_query, "parent_id": parent_id, "is_trashed": is_trashed}
        if is_starred is not None:
            query["is_starred"] = is_starred
        cursor = (
            database.mongodb[settings.CLOUD_DB_NAME]
            .storage_items.find(query)
            .sort([("is_folder", -1), ("name", 1)])
        )
        items = await cursor.to_list(length=None)
        return [StorageItemInDB(**item) for item in items]

    @staticmethod
    @log_logic_execution
    async def search_items(
        query_str: str, owner_id: str, type_filter: Optional[str] = None
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
            database.mongodb[settings.CLOUD_DB_NAME]
            .storage_items.find(query)
            .sort([("created_at", -1)])
        )
        items = await cursor.to_list(length=None)
        return [StorageItemInDB(**item) for item in items]

    @staticmethod
    @log_logic_execution
    async def get_item(
        item_id: str, owner_id: str = None
    ) -> Optional[StorageItemInDB]:
        query = {"_id": item_id}
        if owner_id:
            query["owner_id"] = owner_id
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            query
        )
        if item:
            return StorageItemInDB(**item)
        return None

    @staticmethod
    @log_logic_execution
    async def get_accessible_item(item_id: str, user_id: str) -> Optional[StorageItemInDB]:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({
            "_id": item_id,
            "is_trashed": False,
            "$or": [{"owner_id": user_id}, {"shared_with.user_id": user_id}],
        })
        return StorageItemInDB(**item) if item else None

    @staticmethod
    @log_logic_execution
    async def update_item(
        item_id: str, owner_id: str, update_data: StorageItemUpdate
    ) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return None
        update_dict = update_data.model_dump(exclude_unset=True)
        if "parent_id" in update_dict and update_dict["parent_id"]:
            if update_dict["parent_id"] == item_id:
                return None
            parent = await StorageService.get_item(update_dict["parent_id"], owner_id)
            if not parent or not parent.is_folder or parent.is_trashed:
                return None
            ancestor = parent
            while ancestor.parent_id:
                if ancestor.parent_id == item_id:
                    return None
                ancestor = await StorageService.get_item(ancestor.parent_id, owner_id)
                if not ancestor:
                    return None
        if not update_dict:
            return await StorageService.get_item(item_id, owner_id)
        update_dict["updated_at"] = datetime.now(timezone.utc)
        result = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one_and_update(
            {"_id": item_id, "owner_id": owner_id},
            {"$set": update_dict},
            return_document=True,
        )
        if result:
            if item.is_folder and "is_trashed" in update_dict:
                pending = [item_id]
                descendant_ids = []
                while pending:
                    children = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(
                        {"owner_id": owner_id, "parent_id": {"$in": pending}}, {"_id": 1}
                    ).to_list(length=None)
                    pending = [child["_id"] for child in children]
                    descendant_ids.extend(pending)
                if descendant_ids:
                    await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_many(
                        {"_id": {"$in": descendant_ids}, "owner_id": owner_id},
                        {"$set": {"is_trashed": update_dict["is_trashed"], "updated_at": datetime.now(timezone.utc)}},
                    )
            return StorageItemInDB(**result)
        return None

    @staticmethod
    @log_logic_execution
    async def delete_item(item_id: str, owner_id: str) -> bool:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return False

        items = [item]
        if item.is_folder:
            pending = [item.id]
            while pending:
                children = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(
                    {"owner_id": owner_id, "parent_id": {"$in": pending}}
                ).to_list(length=None)
                pending = []
                for child in children:
                    parsed = StorageItemInDB(**child)
                    items.append(parsed)
                    if parsed.is_folder:
                        pending.append(parsed.id)
        ids = [entry.id for entry in items]
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.delete_many(
            {"_id": {"$in": ids}, "owner_id": owner_id}
        )
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.delete_many(
            {"target_id": {"$in": ids}}
        )
        from src.core.storage import get_bucket, get_storage_client
        storage_client = await get_storage_client()
        for entry in items:
            urls = []
            if not entry.is_folder and not entry.is_shortcut and entry.url:
                urls.append(entry.url)
                urls.extend(version.url for version in entry.versions if version.url != entry.url)
            for url in urls:
                references = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.count_documents({"url": url})
                if references == 0:
                    try:
                        await storage_client.delete_object(Bucket=get_bucket(url), Key=url)
                    except Exception:
                        logger.exception("Failed to cleanup physical storage file")
        return True

    @staticmethod
    @log_logic_execution
    async def _copy_children(source_parent_id: str, new_parent_id: str, owner_id: str):
        cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(
            {"owner_id": owner_id, "parent_id": source_parent_id, "is_trashed": False}
        )
        children = await cursor.to_list(length=None)
        for child in children:
            child_dict = StorageItemInDB(**child).model_dump()
            child_id_old = child_dict.pop("id", None)
            child_dict["parent_id"] = new_parent_id
            new_child = StorageItemInDB(**child_dict)
            await database.mongodb[settings.CLOUD_DB_NAME].storage_items.insert_one(
                new_child.model_dump(by_alias=True)
            )
            if new_child.is_folder:
                await StorageService._copy_children(
                    str(child_id_old), str(new_child.id), owner_id
                )

    @staticmethod
    @log_logic_execution
    async def copy_item(
        item_id: str, owner_id: str, target_parent_id: Optional[str] = None
    ) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return None
        if target_parent_id:
            parent = await StorageService.get_item(target_parent_id, owner_id)
            if not parent or not parent.is_folder or parent.is_trashed:
                return None
        new_item_dict = item.model_dump()
        new_item_dict["name"] = f"{item.name} (Copy)"
        if target_parent_id is not None:
            new_item_dict["parent_id"] = target_parent_id
        new_item_dict.pop("id", None)
        new_item = StorageItemInDB(**new_item_dict)
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.insert_one(
            new_item.model_dump(by_alias=True)
        )
        if item.is_folder:
            await StorageService._copy_children(item_id, str(new_item.id), owner_id)
        return new_item

    @staticmethod
    @log_logic_execution
    async def add_version(
        item_id: str, owner_id: str, url: str, size: int
    ) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")
        if item.is_folder:
            raise HTTPException(
                status_code=400,
                detail="Thư mục không hỗ trợ lịch sử phiên bản",
            )
        if not url.startswith((f"users/{owner_id}/", f"client/{owner_id}/")):
            raise HTTPException(
                status_code=400,
                detail="Đường dẫn phiên bản không thuộc người dùng hiện tại",
            )
        from src.core.storage import get_bucket, get_storage_client
        try:
            client = await get_storage_client()
            metadata = await client.head_object(Bucket=get_bucket(url), Key=url)
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Dịch vụ lưu trữ tạm thời không khả dụng",
            )
        if metadata.get("ContentLength") != size:
            raise HTTPException(
                status_code=409,
                detail="Kích thước phiên bản không khớp với dữ liệu đã tải lên",
            )
        quota = await StorageService.get_storage_quota(owner_id)
        cloud_db = database.mongodb[settings.CLOUD_DB_NAME]
        registered = await cloud_db.storage_items.find_one(
            {
                "owner_id": owner_id,
                "$or": [{"url": url}, {"versions.url": url}],
            },
            {"_id": 1},
        )
        projected_usage = quota["used"] if registered else quota["used"] + size
        if projected_usage > quota["limit"]:
            raise HTTPException(
                status_code=413,
                detail="Dung lượng lưu trữ còn lại không đủ",
            )
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
                "versions": {"$each": [old_version.model_dump()], "$slice": -10}
            }

        size_diff = size - (item.size or 0)
        async with await database.mongodb.start_session() as session:
            async with session.start_transaction():
                await cloud_db.storage_items.update_one(
                    {"_id": item_id, "owner_id": owner_id},
                    update_op,
                    session=session,
                )
                if registered and str(registered["_id"]) != item_id:
                    await cloud_db.storage_items.delete_one(
                        {"_id": registered["_id"], "owner_id": owner_id},
                        session=session,
                    )

        return await StorageService.get_item(item_id, owner_id)

    @staticmethod
    @log_logic_execution
    async def get_public_item(share_token: str) -> Optional[StorageItemInDB]:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"share_token": share_token, "is_public": True}
        )
        if item:
            return StorageItemInDB(**item)
        return None

    @staticmethod
    @log_logic_execution
    async def share_item(
        item_id: str, email: str, role: str, owner_id: str
    ) -> dict:
        if role not in {"viewer", "editor"}:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="Vai trò chia sẻ không hợp lệ")
        target_user = await UserDirectory.get_by_email(email)
        if not target_user:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài khoản người dùng tương ứng với email"
            )
        target_user_id = str(target_user["_id"])
        if target_user_id == owner_id:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400, detail="Không thể tự chia sẻ tài liệu cho chính mình"
            )
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"_id": item_id, "owner_id": owner_id}
        )
        if not item:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail="Không tìm thấy dữ liệu hoặc thiếu quyền chia sẻ"
            )
        result = (
            await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
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
        return {"message": "Chia sẻ tệp hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_recent_items(
        owner_id: str,
        limit: int = Query(
            default=20, le=100
        ),
    ) -> List[StorageItemInDB]:
        query = {
            "$or": [{"owner_id": owner_id}, {"shared_with.user_id": owner_id}],
            "is_trashed": False,
            "is_folder": False,
        }
        cursor = (
            database.mongodb[settings.CLOUD_DB_NAME]
            .storage_items.find(query)
            .sort([("updated_at", -1)])
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        return [StorageItemInDB(**item) for item in items]
