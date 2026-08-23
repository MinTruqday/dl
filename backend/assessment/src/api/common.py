from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from pymongo import ReturnDocument

from src.core.auth import CurrentUser
from src.core.database import database
from src.core.metrics import metrics


def new_id(prefix: str):
    return f"{prefix}-{uuid4().hex}"


def now():
    return datetime.now(timezone.utc)


async def require_owned(collection: str, entity_id: str, user: CurrentUser):
    entity = await database.value[collection].find_one({"_id": entity_id})
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy dữ liệu")
    owner_id = entity.get("owner_id") or entity.get("teacher_id") or entity.get("student_id")
    if owner_id and owner_id != user.id and not user.is_admin:
        metrics.increment("cross_tenant_filter_denials")
        await audit(
            user.id,
            "cross_tenant_access_denied",
            collection,
            entity_id,
            {"requested_operation": "read_or_write"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền truy cập dữ liệu"
        )
    return entity


async def audit(
    user_id: str, action: str, entity_type: str, entity_id: str, details: dict | None = None
):
    event = {
        "_id": new_id("AUD"),
        "actor_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
        "created_at": now(),
    }
    await database.value.audit_events.insert_one(event)
    return event


async def optimistic_patch(
    collection: str, entity_id: str, owner_id: str, expected_revision: int, changes: dict
):
    changes = {
        key: value
        for key, value in changes.items()
        if value is not None and key != "expected_revision"
    }
    changes["updated_at"] = now()
    entity = await database.value[collection].find_one_and_update(
        {"_id": entity_id, "owner_id": owner_id, "revision": expected_revision},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if entity:
        return entity
    existing = await database.value[collection].find_one({"_id": entity_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu")
    if existing.get("owner_id") != owner_id:
        metrics.increment("cross_tenant_filter_denials")
        await audit(
            owner_id,
            "cross_tenant_mutation_denied",
            collection,
            entity_id,
            {"requested_operation": "optimistic_patch"},
        )
        raise HTTPException(status_code=403, detail="Không có quyền chỉnh sửa")
    raise HTTPException(
        status_code=409,
        detail={"code": "revision_conflict", "current_revision": existing.get("revision")},
    )
