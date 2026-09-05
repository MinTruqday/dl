from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, new_id, now, optimistic_patch
from src.core.database import database
from src.domain.schemas import (
    NotificationWatchInput,
    ProjectNotificationPreferencePatch,
    ProjectNotificationRulePatch,
)


router = APIRouter(prefix="/kiem-thu", tags=["Thông báo dự án"])

ARTIFACT_COLLECTIONS = {
    "requirement": "requirements",
    "test_case": "test_cases",
    "test_run": "test_runs",
    "defect": "defects",
}


async def require_artifact(project_id, artifact_type, artifact_id):
    collection = ARTIFACT_COLLECTIONS.get(artifact_type)
    if not collection:
        raise HTTPException(status_code=422, detail={"code": "NOTIFICATION_ARTIFACT_TYPE_INVALID"})
    artifact = await database.value[collection].find_one(
        {"_id": artifact_id, "project_id": project_id}, {"_id": 1}
    )
    if not artifact:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})


def default_rules(project_id):
    return {
        "_id": f"PNRULE:{project_id}",
        "project_id": project_id,
        "enabled_events": [],
        "channels": ["in_app"],
        "target_roles": ["QA_LEAD"],
        "escalation_minutes": None,
        "revision": 0,
    }


def default_preferences(project_id, user_id):
    return {
        "_id": f"NPREF:{project_id}:{user_id}",
        "project_id": project_id,
        "user_id": user_id,
        "digest_frequency": "immediate",
        "channels": ["in_app"],
        "muted_events": [],
        "quiet_hours_start": None,
        "quiet_hours_end": None,
        "timezone": "Asia/Ho_Chi_Minh",
        "revision": 0,
    }


@router.get("/du-an/{project_id}/thong-bao/theo-doi")
async def list_notification_watches(
    project_id: str,
    artifact_type: str = Query(default="", max_length=40),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "notification.watch.manage")
    query = {"project_id": project_id, "user_id": user.id}
    if artifact_type:
        if artifact_type not in ARTIFACT_COLLECTIONS:
            raise HTTPException(
                status_code=422,
                detail={"code": "NOTIFICATION_ARTIFACT_TYPE_INVALID"},
            )
        query["artifact_type"] = artifact_type
    items = await database.value.notification_subscriptions.find(query).sort(
        "updated_at", -1
    ).to_list(1000)
    return envelope(items)


@router.put(
    "/du-an/{project_id}/thong-bao/theo-doi/{artifact_type}/{artifact_id}"
)
async def set_notification_watch(
    project_id: str,
    artifact_type: str,
    artifact_id: str,
    payload: NotificationWatchInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "notification.watch.manage")
    await require_artifact(project_id, artifact_type, artifact_id)
    scope = {
        "project_id": project_id,
        "user_id": user.id,
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
    }
    if not payload.watching:
        await database.value.notification_subscriptions.delete_one(scope)
        await audit(
            user.id,
            "notification_watch_removed",
            artifact_type,
            artifact_id,
            project_id,
        )
        return envelope({**scope, "watching": False})
    timestamp = now()
    subscription = await database.value.notification_subscriptions.find_one_and_update(
        scope,
        {
            "$set": {"updated_at": timestamp},
            "$setOnInsert": {
                "_id": new_id("NSUB"),
                **scope,
                "created_at": timestamp,
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    await audit(
        user.id,
        "notification_watch_added",
        artifact_type,
        artifact_id,
        project_id,
    )
    return envelope({**subscription, "watching": True})


@router.get("/du-an/{project_id}/thong-bao/quy-tac")
async def get_project_notification_rules(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "notification.project_rule.manage")
    value = await database.value.project_notification_rules.find_one(
        {"project_id": project_id}
    )
    return envelope(value or default_rules(project_id), revision=(value or {}).get("revision", 0))


@router.patch("/du-an/{project_id}/thong-bao/quy-tac")
async def update_project_notification_rules(
    project_id: str,
    payload: ProjectNotificationRulePatch,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "notification.project_rule.manage")
    current = await database.value.project_notification_rules.find_one(
        {"project_id": project_id}
    )
    changes = payload.model_dump(exclude={"expected_revision"})
    if current:
        updated = await optimistic_patch(
            "project_notification_rules",
            current["_id"],
            project_id,
            payload.expected_revision,
            changes,
        )
    else:
        if payload.expected_revision != 0:
            raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
        timestamp = now()
        updated = {
            **default_rules(project_id),
            **changes,
            "revision": 1,
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await database.value.project_notification_rules.insert_one(updated)
        except DuplicateKeyError:
            raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "project_notification_rules_updated",
        "ProjectNotificationRule",
        updated["_id"],
        project_id,
    )
    return envelope(updated, revision=updated["revision"])


@router.get("/du-an/{project_id}/thong-bao/tuy-chon")
async def get_project_notification_preferences(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "notification.preferences.manage")
    value = await database.value.project_notification_preferences.find_one(
        {"project_id": project_id, "user_id": user.id}
    )
    return envelope(
        value or default_preferences(project_id, user.id),
        revision=(value or {}).get("revision", 0),
    )


@router.patch("/du-an/{project_id}/thong-bao/tuy-chon")
async def update_project_notification_preferences(
    project_id: str,
    payload: ProjectNotificationPreferencePatch,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "notification.preferences.manage")
    current = await database.value.project_notification_preferences.find_one(
        {"project_id": project_id, "user_id": user.id}
    )
    changes = payload.model_dump(exclude={"expected_revision"})
    if current:
        updated = await optimistic_patch(
            "project_notification_preferences",
            current["_id"],
            project_id,
            payload.expected_revision,
            changes,
        )
    else:
        if payload.expected_revision != 0:
            raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
        timestamp = now()
        updated = {
            **default_preferences(project_id, user.id),
            **changes,
            "revision": 1,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await database.value.project_notification_preferences.insert_one(updated)
        except DuplicateKeyError:
            raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "project_notification_preferences_updated",
        "ProjectNotificationPreference",
        updated["_id"],
        project_id,
    )
    return envelope(updated, revision=updated["revision"])
