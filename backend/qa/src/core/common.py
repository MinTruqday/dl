from datetime import datetime, timezone
from math import ceil
from uuid import uuid4

from fastapi import HTTPException
from pymongo import ReturnDocument

from src.core.auth import CurrentUser, READ_PERMISSIONS, permissions_for_role
from src.core.database import database


RETRYABLE_ERROR_CODES = {
    "WORKER_UNAVAILABLE",
    "QDRANT_UNAVAILABLE",
    "RAG_INDEX_FAILED",
    "AI_PROVIDER_UNAVAILABLE",
    "PROPOSAL_APPLY_PARTIAL",
    "WORKER_JOB_FAILED",
}


def new_id(prefix: str):
    return f"{prefix}-{uuid4().hex}"


def now():
    return datetime.now(timezone.utc)


def envelope(
    data=None,
    revision=None,
    trace_id=None,
    status="SUCCESS",
    error_code=None,
    retryable=False,
    state_after_failure=None,
    user_action_required=False,
    degraded_mode=None,
):
    meta = {"trace_id": trace_id or new_id("TRC")}
    if revision is not None:
        meta["revision"] = revision
    operation = {
        "status": status,
        "error_code": error_code,
        "retryable": retryable,
        "state_after_failure": state_after_failure,
        "user_action_required": user_action_required,
    }
    if degraded_mode:
        operation["degraded_mode"] = degraded_mode
    meta["operation"] = operation
    return {"data": data, "meta": meta, **operation}


def page_payload(items, page, page_size, total):
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }


def sort_spec(value, allowed, default="-updated_at"):
    selected = value or default
    descending = selected.startswith("-")
    field = selected[1:] if descending else selected
    if field not in allowed:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_SORT_FIELD", "allowed": sorted(allowed)},
        )
    return field, -1 if descending else 1


def failure_metadata(code, status_code=500, detail=None):
    detail = detail if isinstance(detail, dict) else {}
    retryable = detail.get("retryable", code in RETRYABLE_ERROR_CODES or status_code in {502, 503, 504})
    state_after_failure = detail.get("state_after_failure") or ("UNCHANGED" if status_code < 500 else "RETRYABLE_FAILURE")
    user_action_required = detail.get("user_action_required", status_code in {409, 422, 403} or not retryable)
    return {
        "status": "FAILED",
        "error_code": code,
        "retryable": retryable,
        "state_after_failure": state_after_failure,
        "user_action_required": user_action_required,
    }


async def audit(
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    project_id: str | None,
    details: dict | None = None,
):
    event = {
        "_id": new_id("AUD"),
        "project_id": project_id,
        "actor_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
        "created_at": now(),
    }
    await database.value.audit_events.insert_one(event)
    return event


async def get_project(
    project_id: str,
    user: CurrentUser,
    permission: str = "project.read",
    assigned_role: str | None = None,
    assigned_user_id: str | None = None,
):
    project = await database.value.projects.find_one({"_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    membership = await database.value.project_members.find_one(
        {
            "project_id": project_id,
            "user_id": user.id,
        }
    )
    if not membership:
        await audit(
            user.id,
            "project_membership_required",
            "Project",
            project_id,
            project_id,
            {"permission": permission, "system_role": user.system_role.value},
        )
        raise HTTPException(
            status_code=403,
            detail={"code": "PROJECT_MEMBERSHIP_REQUIRED"},
        )
    if membership.get("status") != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail={"code": "PROJECT_MEMBERSHIP_INACTIVE"},
        )
    permissions = permissions_for_role(
        membership.get("project_role", ""),
        project.get("settings"),
    )
    assigned_access = (
        assigned_role is not None
        and membership.get("project_role") == assigned_role
        and assigned_user_id == user.id
    )
    if permission not in permissions and not assigned_access:
        await audit(
            user.id,
            "project_permission_denied",
            "Project",
            project_id,
            project_id,
            {
                "permission": permission,
                "project_role": membership.get("project_role"),
            },
        )
        raise HTTPException(
            status_code=403,
            detail={"code": "PROJECT_PERMISSION_DENIED", "permission": permission},
        )
    if project.get("status", "active").lower() == "archived" and permission not in READ_PERMISSIONS:
        raise HTTPException(status_code=409, detail={"code": "PROJECT_ARCHIVED"})
    return project


async def get_project_entity(
    collection: str,
    entity_id: str,
    user: CurrentUser,
    permission: str,
    assigned_role: str | None = None,
    assigned_user_field: str | None = None,
):
    projection = {"_id": 1, "project_id": 1}
    if assigned_user_field:
        projection[assigned_user_field] = 1
    identity = await database.value[collection].find_one(
        {"_id": entity_id},
        projection,
    )
    if not identity:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(
        identity["project_id"],
        user,
        permission,
        assigned_role=assigned_role,
        assigned_user_id=identity.get(assigned_user_field) if assigned_user_field else None,
    )
    entity = await database.value[collection].find_one(
        {"_id": entity_id, "project_id": identity["project_id"]}
    )
    if not entity:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    return entity


async def optimistic_patch(
    collection: str,
    entity_id: str,
    project_id: str,
    expected_revision: int,
    changes: dict,
):
    cleaned = {
        key: value
        for key, value in changes.items()
        if value is not None and key != "expected_revision"
    }
    cleaned["updated_at"] = now()
    scope = {"_id": entity_id, "revision": expected_revision}
    if collection != "projects":
        scope["project_id"] = project_id
    entity = await database.value[collection].find_one_and_update(
        scope,
        {"$set": cleaned, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if entity:
        return entity
    existing = await database.value[collection].find_one({"_id": entity_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu")
    raise HTTPException(
        status_code=409,
        detail={"code": "REVISION_CONFLICT", "current_revision": existing.get("revision")},
    )


async def next_key(project_id: str, sequence: str, prefix: str):
    value = await database.value.counters.find_one_and_update(
        {"_id": f"{project_id}:{sequence}"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return f"{prefix}-{int(value['value']):04d}"


def plain_text(document):
    values = []

    def visit(node):
        if isinstance(node, dict):
            if isinstance(node.get("text"), str):
                values.append(node["text"])
            for child in node.get("content", []):
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(document)
    return " ".join(values).strip()


def validate_doc(value):
    if not isinstance(value, dict) or value.get("type") != "doc" or not isinstance(
        value.get("content", []), list
    ):
        raise HTTPException(status_code=422, detail="Tiptap JSON không hợp lệ")
    return value
