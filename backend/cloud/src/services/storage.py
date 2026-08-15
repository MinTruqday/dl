from src.clients.humanity import HumanityClient
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
            from src.core.storage import get_bucket, get_storage_client, original_content_length
            try:
                client = await get_storage_client()
                metadata = await client.head_object(Bucket=get_bucket(item.url), Key=item.url)
            except Exception:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Không tìm thấy dữ liệu tệp trong kho đối tượng")
            if original_content_length(metadata) != item.size:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Kích thước tệp không khớp dữ liệu lưu trữ")
        db_item = StorageItemInDB(**item.model_dump(), owner_id=owner_id)
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.insert_one(
            db_item.model_dump(by_alias=True)
        )
        return db_item

    @staticmethod
    async def get_storage_quota(owner_id: str) -> dict:
        user = await HumanityClient.get_by_id(owner_id)
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
    async def get_items_by_parent(
        parent_id: Optional[str],
        owner_id: str,
        is_trashed: bool = False,
        is_starred: Optional[bool] = None,
        tag: Optional[str] = None,
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
        if tag:
            query["tags"] = tag
        cursor = (
            database.mongodb[settings.CLOUD_DB_NAME]
            .storage_items.find(query)
            .sort([("is_folder", -1), ("name", 1)])
        )
        items = await cursor.to_list(length=None)
        return [StorageItemInDB(**item) for item in items]

    @staticmethod
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
    async def get_accessible_item(item_id: str, user_id: str) -> Optional[StorageItemInDB]:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({
            "_id": item_id,
            "is_trashed": False,
            "$or": [{"owner_id": user_id}, {"shared_with.user_id": user_id}],
        })
        return StorageItemInDB(**item) if item else None

    @staticmethod
    async def update_item(
        item_id: str, owner_id: str, update_data: StorageItemUpdate
    ) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return None
        
        if item.is_locked and item.locked_by != owner_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Tệp đang bị khóa bởi người dùng khác")

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
    async def delete_item(item_id: str, owner_id: str) -> bool:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            return False

        if item.is_locked and item.locked_by != owner_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Tệp đang bị khóa bởi người dùng khác, không thể xóa")

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
        from src.core.storage import get_bucket, get_storage_client, original_content_length
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
        from src.core.storage import get_bucket, get_storage_client, original_content_length
        try:
            client = await get_storage_client()
            metadata = await client.head_object(Bucket=get_bucket(url), Key=url)
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Dịch vụ lưu trữ tạm thời không khả dụng",
            )
        if original_content_length(metadata) != size:
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
    async def get_public_item(share_token: str) -> Optional[StorageItemInDB]:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"share_token": share_token, "is_public": True}
        )
        if item:
            return StorageItemInDB(**item)
        return None

    @staticmethod
    async def share_item(
        item_id: str, email: str, role: str, owner_id: str
    ) -> dict:
        if role not in {"viewer", "editor"}:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="Vai trò chia sẻ không hợp lệ")
        target_user = await HumanityClient.get_by_email(email)
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

    @staticmethod
    async def lock_item(item_id: str, owner_id: str) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item or item.is_folder:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Chỉ có thể khóa tệp tin, không áp dụng cho thư mục")
        if item.is_locked:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Tệp tin đã bị khóa")
        
        result = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one_and_update(
            {"_id": item_id, "owner_id": owner_id},
            {"$set": {"is_locked": True, "locked_by": owner_id, "locked_at": datetime.now(timezone.utc)}},
            return_document=True,
        )
        return StorageItemInDB(**result) if result else None

    @staticmethod
    async def unlock_item(item_id: str, owner_id: str) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item or item.is_folder:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Không tìm thấy tệp tin")
        if not item.is_locked:
            return item
        if item.locked_by != owner_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Chỉ người đã khóa tệp mới có quyền mở khóa")
        
        result = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one_and_update(
            {"_id": item_id, "owner_id": owner_id},
            {"$set": {"is_locked": False, "locked_by": None, "locked_at": None}},
            return_document=True,
        )
        return StorageItemInDB(**result) if result else None

    @staticmethod
    async def bulk_action(action: str, item_ids: List[str], target_parent_id: Optional[str], owner_id: str) -> dict:
        success_count = 0
        failed_count = 0
        for i_id in item_ids:
            try:
                if action == "delete":
                    res = await StorageService.update_item(i_id, owner_id, StorageItemUpdate(is_trashed=True))
                    if res: success_count += 1
                    else: failed_count += 1
                elif action == "move":
                    res = await StorageService.update_item(i_id, owner_id, StorageItemUpdate(parent_id=target_parent_id))
                    if res: success_count += 1
                    else: failed_count += 1
                elif action == "copy":
                    res = await StorageService.copy_item(i_id, owner_id, target_parent_id)
                    if res: success_count += 1
                    else: failed_count += 1
            except Exception:
                failed_count += 1
        return {"success": success_count, "failed": failed_count}

    @staticmethod
    async def get_versions(item_id: str, user_id: str) -> List[dict]:
        item = await StorageService.get_accessible_item(item_id, user_id)
        if not item or item.is_folder:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin hoặc thư mục không hỗ trợ phiên bản")
        
        results = [
            {
                "version_id": "current",
                "url": item.url,
                "size": item.size,
                "created_at": item.updated_at or item.created_at,
                "is_active": True,
            }
        ]
        for v in (item.versions or []):
            results.append({
                "version_id": v.version_id,
                "url": v.url,
                "size": v.size,
                "created_at": v.created_at,
                "is_active": False,
            })
        return results

    @staticmethod
    async def rollback_version(item_id: str, version_id: str, owner_id: str) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item or item.is_folder:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")
        if item.is_locked and item.locked_by != owner_id:
            raise HTTPException(status_code=403, detail="Tệp đang bị khóa bởi người dùng khác")
        
        target_version = None
        remaining_versions = []
        for v in (item.versions or []):
            if v.version_id == version_id:
                target_version = v
            else:
                remaining_versions.append(v)
        
        if not target_version:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản yêu cầu khôi phục")
        
        from src.schemas.storage import FileVersion
        archived_current = FileVersion(
            url=item.url,
            size=item.size,
            created_at=item.updated_at or item.created_at
        )
        remaining_versions.insert(0, archived_current)
        
        now = datetime.now(timezone.utc)
        result = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one_and_update(
            {"_id": item_id, "owner_id": owner_id},
            {
                "$set": {
                    "url": target_version.url,
                    "size": target_version.size,
                    "versions": [v.model_dump() for v in remaining_versions[:10]],
                    "updated_at": now
                }
            },
            return_document=True
        )
        from src.services.activity import ActivityService
        await ActivityService.log_activity(item_id, owner_id, "ROLLBACK_VERSION")
        return StorageItemInDB(**result) if result else None

    @staticmethod
    async def set_starred(item_id: str, is_starred: bool, owner_id: str) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp hoặc thư mục")
        
        result = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one_and_update(
            {"_id": item_id, "owner_id": owner_id},
            {"$set": {"is_starred": is_starred, "updated_at": datetime.now(timezone.utc)}},
            return_document=True
        )
        from src.services.activity import ActivityService
        await ActivityService.log_activity(item_id, owner_id, "STAR" if is_starred else "UNSTAR")
        return StorageItemInDB(**result) if result else None

    @staticmethod
    async def set_tags_and_color(
        item_id: str,
        tags: Optional[List[str]],
        color: Optional[str],
        owner_id: str
    ) -> Optional[StorageItemInDB]:
        item = await StorageService.get_item(item_id, owner_id)
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp hoặc thư mục")
        
        update_set = {"updated_at": datetime.now(timezone.utc)}
        if tags is not None:
            update_set["tags"] = tags
        if color is not None:
            update_set["color"] = color
        
        result = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one_and_update(
            {"_id": item_id, "owner_id": owner_id},
            {"$set": update_set},
            return_document=True
        )
        from src.services.activity import ActivityService
        if tags is not None:
            await ActivityService.log_activity(item_id, owner_id, "TAG")
        if color is not None:
            await ActivityService.log_activity(item_id, owner_id, "COLOR")
        return StorageItemInDB(**result) if result else None

    @staticmethod
    async def get_trashed_items(owner_id: str) -> List[StorageItemInDB]:
        cursor = (
            database.mongodb[settings.CLOUD_DB_NAME]
            .storage_items.find({"owner_id": owner_id, "is_trashed": True})
            .sort([("updated_at", -1)])
        )
        items = await cursor.to_list(length=None)
        return [StorageItemInDB(**item) for item in items]

    @staticmethod
    async def restore_from_trash(item_id: str, owner_id: str) -> Optional[StorageItemInDB]:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"_id": item_id, "owner_id": owner_id, "is_trashed": True}
        )
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp trong thùng rác")
        
        parsed = StorageItemInDB(**item)
        items_to_restore = [parsed.id]
        if parsed.is_folder:
            pending = [parsed.id]
            while pending:
                children = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(
                    {"owner_id": owner_id, "parent_id": {"$in": pending}}, {"_id": 1, "is_folder": 1}
                ).to_list(length=None)
                pending = [child["_id"] for child in children if child.get("is_folder")]
                items_to_restore.extend(child["_id"] for child in children)
        
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_many(
            {"_id": {"$in": items_to_restore}, "owner_id": owner_id},
            {"$set": {"is_trashed": False, "updated_at": datetime.now(timezone.utc)}}
        )
        from src.services.activity import ActivityService
        await ActivityService.log_activity(item_id, owner_id, "RESTORE_TRASH")
        return await StorageService.get_item(item_id, owner_id)

    @staticmethod
    async def empty_trash(owner_id: str) -> dict:
        cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(
            {"owner_id": owner_id, "is_trashed": True}
        )
        items = await cursor.to_list(length=None)
        if not items:
            return {"deleted_count": 0}
        
        parsed_items = [StorageItemInDB(**i) for i in items]
        ids = [i.id for i in parsed_items]
        
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.delete_many(
            {"_id": {"$in": ids}, "owner_id": owner_id}
        )
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.delete_many(
            {"target_id": {"$in": ids}}
        )
        
        from src.core.storage import get_bucket, get_storage_client
        storage_client = await get_storage_client()
        for entry in parsed_items:
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
                        logger.exception("Failed to cleanup physical storage file from trash")
        
        from src.services.activity import ActivityService
        await ActivityService.log_activity("system", owner_id, "EMPTY_TRASH")
        return {"deleted_count": len(ids)}

    @staticmethod
    async def get_quota_analytics(owner_id: str) -> dict:
        quota = await StorageService.get_storage_quota(owner_id)
        total_limit = quota["limit"]
        total_used = quota["used"]
        free_bytes = max(0, total_limit - total_used)
        usage_pct = round((total_used / total_limit * 100) if total_limit > 0 else 0.0, 2)
        
        categories = {
            "documents": {"extensions": [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".pages", ".md"], "count": 0, "size": 0},
            "images": {"extensions": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"], "count": 0, "size": 0},
            "videos": {"extensions": [".mp4", ".mkv", ".mov", ".avi", ".webm"], "count": 0, "size": 0},
            "audio": {"extensions": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"], "count": 0, "size": 0},
            "archives": {"extensions": [".zip", ".rar", ".7z", ".tar", ".gz"], "count": 0, "size": 0},
            "code": {"extensions": [".py", ".ts", ".js", ".json", ".html", ".css", ".cpp", ".java", ".sql", ".sh", ".yml", ".yaml"], "count": 0, "size": 0},
            "others": {"extensions": [], "count": 0, "size": 0}
        }
        
        cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(
            {"owner_id": owner_id, "is_folder": False, "is_trashed": False}
        )
        files = await cursor.to_list(length=None)
        total_files = len(files)
        
        for f in files:
            name = (f.get("name") or "").lower()
            size = f.get("size") or 0
            for v in f.get("versions", []):
                size += (v.get("size") or 0)
            
            matched = False
            for cat_name, cat_data in categories.items():
                if cat_name == "others": continue
                if any(name.endswith(ext) for ext in cat_data["extensions"]):
                    cat_data["count"] += 1
                    cat_data["size"] += size
                    matched = True
                    break
            if not matched:
                categories["others"]["count"] += 1
                categories["others"]["size"] += size
        
        breakdown_result = {}
        for cat_name, cat_data in categories.items():
            breakdown_result[cat_name] = {
                "count": cat_data["count"],
                "size": cat_data["size"],
                "percentage": round((cat_data["size"] / total_used * 100) if total_used > 0 else 0.0, 2)
            }
        
        total_folders = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.count_documents(
            {"owner_id": owner_id, "is_folder": True, "is_trashed": False}
        )
        
        trashed_cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(
            {"owner_id": owner_id, "is_trashed": True, "is_folder": False}
        )
        trashed_files = await trashed_cursor.to_list(length=None)
        trashed_bytes = sum((t.get("size") or 0) for t in trashed_files)
        
        return {
            "total_quota_bytes": total_limit,
            "used_quota_bytes": total_used,
            "free_quota_bytes": free_bytes,
            "usage_percentage": usage_pct,
            "total_files_count": total_files,
            "total_folders_count": total_folders,
            "trashed_files_count": len(trashed_files),
            "trashed_bytes": trashed_bytes,
            "breakdown": breakdown_result
        }

    @staticmethod
    async def share_internal(
        item_id: str, email: str, role: str, owner_id: str
    ) -> dict:
        return await StorageService.share_item(item_id, email, role, owner_id)

    @staticmethod
    async def revoke_internal_share(
        item_id: str, target_user_id: str, owner_id: str
    ) -> bool:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"_id": item_id, "owner_id": owner_id}
        )
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp hoặc thiếu quyền")
        
        res = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": item_id, "owner_id": owner_id},
            {"$pull": {"shared_with": {"user_id": target_user_id}}}
        )
        from src.services.activity import ActivityService
        await ActivityService.log_activity(item_id, owner_id, "REVOKE_SHARE")
        return res.modified_count > 0

    @staticmethod
    async def get_shared_with_me_items(user_id: str) -> List[StorageItemInDB]:
        cursor = (
            database.mongodb[settings.CLOUD_DB_NAME]
            .storage_items.find({
                "shared_with.user_id": user_id,
                "is_trashed": False
            })
            .sort([("updated_at", -1)])
        )
        items = await cursor.to_list(length=None)
        return [StorageItemInDB(**item) for item in items]
