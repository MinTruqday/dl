from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.domain.schemas import (
    ConnectorConflictResolution,
    ConnectorSyncInput,
    ProjectConnectorCreate,
    ProjectConnectorPatch,
    ProjectConnectorUnbind,
)


router = APIRouter(prefix="/kiem-thu", tags=["Kết nối dự án"])


def public_connector(value):
    result = dict(value)
    result["connector_reference"] = "Đã cấu hình"
    return result


@router.get("/du-an/{project_id}/ket-noi")
async def list_project_connectors(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.connector.read")
    items = await database.value.project_connectors.find(
        {"project_id": project_id}
    ).sort("updated_at", -1).to_list(100)
    return envelope([public_connector(item) for item in items])


@router.post("/du-an/{project_id}/ket-noi", status_code=201)
async def bind_project_connector(
    project_id: str,
    payload: ProjectConnectorCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.connector.manage")
    timestamp = now()
    value = {
        "_id": new_id("CONN"),
        "project_id": project_id,
        "provider": payload.provider,
        "connector_reference": payload.connector_reference,
        "external_target": payload.external_target,
        "field_mapping": payload.field_mapping,
        "mapping_version": 1,
        "mapping_versions": [
            {
                "version": 1,
                "field_mapping": payload.field_mapping,
                "created_by": user.id,
                "created_at": timestamp,
            }
        ],
        "status": "BOUND",
        "enabled": True,
        "last_cursor": None,
        "last_sync_status": "NEVER",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.project_connectors.insert_one(value)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "CONNECTOR_ALREADY_BOUND"})
    await audit(
        user.id,
        "project_connector_bound",
        "ProjectConnector",
        value["_id"],
        project_id,
        {"provider": payload.provider, "external_target": payload.external_target},
    )
    return envelope(public_connector(value), revision=1)


@router.patch("/du-an/{project_id}/ket-noi/{connector_id}")
async def update_project_connector(
    project_id: str,
    connector_id: str,
    payload: ProjectConnectorPatch,
    user: CurrentUser = Depends(get_current_user),
):
    connector = await get_project_entity(
        "project_connectors", connector_id, user, "project.connector.manage"
    )
    if connector["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    changes.pop("confirm_external_target", None)
    if payload.field_mapping is not None:
        mapping_version = connector.get("mapping_version", 1) + 1
        changes["mapping_version"] = mapping_version
        changes["mapping_versions"] = [
            *connector.get("mapping_versions", []),
            {
                "version": mapping_version,
                "field_mapping": payload.field_mapping,
                "created_by": user.id,
                "created_at": now(),
            },
        ]
    updated = await database.value.project_connectors.find_one_and_update(
        {
            "_id": connector_id,
            "project_id": project_id,
            "revision": payload.expected_revision,
        },
        {"$set": {**changes, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "project_connector_updated",
        "ProjectConnector",
        connector_id,
        project_id,
        {"mapping_version": updated.get("mapping_version")},
    )
    return envelope(public_connector(updated), revision=updated["revision"])


@router.post("/du-an/{project_id}/ket-noi/{connector_id}/ngat")
async def unbind_project_connector(
    project_id: str,
    connector_id: str,
    payload: ProjectConnectorUnbind,
    user: CurrentUser = Depends(get_current_user),
):
    connector = await get_project_entity(
        "project_connectors", connector_id, user, "project.connector.manage"
    )
    if connector["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if not payload.confirm_external_target:
        raise HTTPException(status_code=422, detail={"code": "TARGET_CONFIRMATION_REQUIRED"})
    updated = await database.value.project_connectors.find_one_and_update(
        {
            "_id": connector_id,
            "project_id": project_id,
            "revision": payload.expected_revision,
            "status": "BOUND",
        },
        {
            "$set": {
                "status": "UNBOUND",
                "enabled": False,
                "unbind_reason": payload.reason,
                "unbound_by": user.id,
                "unbound_at": now(),
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "CONNECTOR_STATE_CONFLICT"})
    await audit(
        user.id,
        "project_connector_unbound",
        "ProjectConnector",
        connector_id,
        project_id,
        {"external_target": connector["external_target"], "reason": payload.reason},
    )
    return envelope(public_connector(updated), revision=updated["revision"])


@router.post("/du-an/{project_id}/ket-noi/{connector_id}/dong-bo", status_code=202)
async def start_connector_sync(
    project_id: str,
    connector_id: str,
    payload: ConnectorSyncInput,
    user: CurrentUser = Depends(get_current_user),
):
    connector = await get_project_entity(
        "project_connectors", connector_id, user, "project.connector.sync"
    )
    if connector["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if connector.get("status") != "BOUND" or not connector.get("enabled"):
        raise HTTPException(status_code=409, detail={"code": "CONNECTOR_NOT_ACTIVE"})
    existing = await database.value.connector_sync_jobs.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        if existing.get("connector_id") != connector_id:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return envelope(existing, operation_id=existing["_id"])
    timestamp = now()
    value = {
        "_id": new_id("SYNC"),
        "project_id": project_id,
        "connector_id": connector_id,
        "direction": payload.direction,
        "scopes": payload.scopes,
        "cursor_before": connector.get("last_cursor"),
        "status": "QUEUED",
        "conflict_aware": True,
        "idempotency_key": payload.idempotency_key,
        "requested_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.connector_sync_jobs.insert_one(value)
    except DuplicateKeyError:
        existing = await database.value.connector_sync_jobs.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            return envelope(existing, operation_id=existing["_id"])
        raise
    await audit(
        user.id,
        "connector_sync_queued",
        "SyncCursor",
        value["_id"],
        project_id,
        {"direction": payload.direction, "scopes": payload.scopes},
    )
    return envelope(value, operation_id=value["_id"])


@router.get("/du-an/{project_id}/ket-noi/nhat-ky")
async def list_connector_sync_log(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.connector.read")
    items = await database.value.connector_sync_jobs.find(
        {"project_id": project_id}
    ).sort("created_at", -1).to_list(1000)
    for item in items:
        item.pop("raw_payload", None)
        item.pop("secret", None)
    return envelope(items)


@router.get("/du-an/{project_id}/ket-noi/xung-dot")
async def list_connector_conflicts(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.connector.review")
    items = await database.value.connector_sync_conflicts.find(
        {"project_id": project_id}
    ).sort("created_at", -1).to_list(1000)
    return envelope(items)


@router.post("/du-an/{project_id}/ket-noi/xung-dot/{conflict_id}/giai-quyet")
async def resolve_connector_conflict(
    project_id: str,
    conflict_id: str,
    payload: ConnectorConflictResolution,
    user: CurrentUser = Depends(get_current_user),
):
    conflict = await get_project_entity(
        "connector_sync_conflicts", conflict_id, user, "project.connector.review"
    )
    if conflict["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    updated = await database.value.connector_sync_conflicts.find_one_and_update(
        {
            "_id": conflict_id,
            "project_id": project_id,
            "revision": payload.expected_revision,
            "status": "OPEN",
        },
        {
            "$set": {
                "status": "RESOLVED",
                "resolution": payload.resolution,
                "merged_value": payload.merged_value,
                "reason": payload.reason,
                "resolved_by": user.id,
                "resolved_at": now(),
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "CONFLICT_ALREADY_RESOLVED"})
    await audit(
        user.id,
        "connector_conflict_resolved",
        "SyncConflict",
        conflict_id,
        project_id,
        {"resolution": payload.resolution, "reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])
