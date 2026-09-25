from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from loguru import logger

from src.core.storage import get_bucket, get_storage_client
from src.repositories import storage_repository
from src.schemas.storage import StorageItemInDB
from src.services.activity import ActivityService


async def _owned_item(item_id: str, owner_id: str) -> Optional[StorageItemInDB]:
    item = await storage_repository.find_one(
        {"_id": item_id, "owner_id": owner_id}
    )
    return StorageItemInDB(**item) if item else None


async def _delete_physical_files(items: list[StorageItemInDB]) -> None:
    storage_client = await get_storage_client()
    for item in items:
        urls = []
        if not item.is_folder and not item.is_shortcut and item.url:
            urls.append(item.url)
            urls.extend(version.url for version in item.versions if version.url != item.url)
        for url in urls:
            if await storage_repository.count({"url": url}) == 0:
                try:
                    await storage_client.delete_object(Bucket=get_bucket(url), Key=url)
                except Exception:
                    logger.exception("Failed to cleanup physical storage file")


async def delete_item(item_id: str, owner_id: str) -> bool:
    item = await _owned_item(item_id, owner_id)
    if not item:
        return False
    if item.is_locked and item.locked_by != owner_id:
        raise HTTPException(
            status_code=403,
            detail="Tệp đang bị khóa bởi người dùng khác, không thể xóa",
        )
    items = [item]
    if item.is_folder:
        pending = [item.id]
        while pending:
            children = await storage_repository.find_many(
                {"owner_id": owner_id, "parent_id": {"$in": pending}}
            )
            pending = []
            for child in children:
                parsed = StorageItemInDB(**child)
                items.append(parsed)
                if parsed.is_folder:
                    pending.append(parsed.id)
    identifiers = [entry.id for entry in items]
    await storage_repository.delete_many(
        {"_id": {"$in": identifiers}, "owner_id": owner_id}
    )
    await storage_repository.delete_many({"target_id": {"$in": identifiers}})
    await _delete_physical_files(items)
    return True


async def get_trashed_items(owner_id: str) -> List[StorageItemInDB]:
    items = await storage_repository.find_many(
        {"owner_id": owner_id, "is_trashed": True},
        sort=[("updated_at", -1)],
    )
    return [StorageItemInDB(**item) for item in items]


async def restore_from_trash(item_id: str, owner_id: str) -> Optional[StorageItemInDB]:
    item = await storage_repository.find_one(
        {"_id": item_id, "owner_id": owner_id, "is_trashed": True}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp trong thùng rác")
    parsed = StorageItemInDB(**item)
    identifiers = [parsed.id]
    if parsed.is_folder:
        pending = [parsed.id]
        while pending:
            children = await storage_repository.find_many(
                {"owner_id": owner_id, "parent_id": {"$in": pending}},
                {"_id": 1, "is_folder": 1},
            )
            pending = [child["_id"] for child in children if child.get("is_folder")]
            identifiers.extend(child["_id"] for child in children)
    await storage_repository.update_many(
        {"_id": {"$in": identifiers}, "owner_id": owner_id},
        {"$set": {"is_trashed": False, "updated_at": datetime.now(timezone.utc)}},
    )
    await ActivityService.log_activity(item_id, owner_id, "RESTORE_TRASH")
    return await _owned_item(item_id, owner_id)


async def empty_trash(owner_id: str) -> dict:
    items = await storage_repository.find_many(
        {"owner_id": owner_id, "is_trashed": True}
    )
    if not items:
        return {"deleted_count": 0}
    parsed_items = [StorageItemInDB(**item) for item in items]
    identifiers = [item.id for item in parsed_items]
    await storage_repository.delete_many(
        {"_id": {"$in": identifiers}, "owner_id": owner_id}
    )
    await storage_repository.delete_many({"target_id": {"$in": identifiers}})
    await _delete_physical_files(parsed_items)
    await ActivityService.log_activity("system", owner_id, "EMPTY_TRASH")
    return {"deleted_count": len(identifiers)}
