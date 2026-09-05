from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.api.requirements import update_requirement_draft
from src.api.test_design import update_test_case_draft
from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.domain.schemas import (
    CollaborationConflictResolution,
    CollaborationOperationInput,
    CollaborationPresenceInput,
    RequirementDraftPatch,
    TestCaseDraftPatch,
)


router = APIRouter(prefix="/kiem-thu", tags=["Cộng tác thời gian thực"])


async def artifact_context(project_id, artifact_type, artifact_id, user, edit=False):
    if artifact_type == "requirement":
        requirement = await get_project_entity(
            "requirements", artifact_id, user, "requirement.update" if edit else "requirement.read"
        )
        if requirement["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
        version = await database.value.requirement_versions.find_one(
            {"_id": requirement["current_version_id"], "project_id": project_id}
        )
        if not version:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
        if edit and version.get("status") != "DRAFT":
            raise HTTPException(status_code=409, detail={"code": "IMMUTABLE_REQUIREMENT_VERSION"})
        return version
    draft = await get_project_entity(
        "test_case_drafts", artifact_id, user, "testcase.update" if edit else "testcase.read"
    )
    if draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if edit and draft.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "IMMUTABLE_TEST_CASE_DRAFT"})
    return draft


@router.put("/du-an/{project_id}/cong-tac/phien")
async def update_collaboration_presence(
    project_id: str,
    payload: CollaborationPresenceInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "collaboration.presence.read")
    await artifact_context(project_id, payload.artifact_type, payload.artifact_id, user)
    timestamp = now()
    value = await database.value.collaboration_sessions.find_one_and_update(
        {
            "project_id": project_id,
            "artifact_type": payload.artifact_type,
            "artifact_id": payload.artifact_id,
            "user_id": user.id,
            "client_id": payload.client_id,
        },
        {
            "$set": {
                "user_email": user.email,
                "last_seen_at": timestamp,
                "expires_at": timestamp + timedelta(seconds=45),
            },
            "$setOnInsert": {"_id": new_id("COLSESS"), "created_at": timestamp},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return envelope(value)


@router.get("/du-an/{project_id}/cong-tac/hien-dien")
async def list_collaboration_presence(
    project_id: str,
    artifact_type: str = Query(pattern="^(requirement|test_case)$"),
    artifact_id: str = Query(min_length=1, max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "collaboration.presence.read")
    await artifact_context(project_id, artifact_type, artifact_id, user)
    items = await database.value.collaboration_sessions.find(
        {
            "project_id": project_id,
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
            "expires_at": {"$gt": now()},
        }
    ).sort("last_seen_at", -1).to_list(100)
    return envelope(items)


async def apply_operation(project_id, artifact_type, artifact_id, payload, user):
    current = await artifact_context(project_id, artifact_type, artifact_id, user, edit=True)
    existing = await database.value.collaboration_operations.find_one(
        {"project_id": project_id, "operation_id": payload.operation_id}
    )
    if existing:
        return existing["result"]
    current_revision = current["revision"]
    changes = payload.changes
    rebased = False
    if payload.base_revision != current_revision:
        operations = await database.value.collaboration_operations.find(
            {
                "project_id": project_id,
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,
                "result_revision": {"$gt": payload.base_revision},
            }
        ).to_list(10000)
        changed_keys = {key for operation in operations for key in operation.get("changed_keys", [])}
        if changed_keys.isdisjoint(changes):
            rebased = True
        else:
            conflict = {
                "_id": new_id("DRAFTCONFLICT"),
                "project_id": project_id,
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,
                "base_revision": payload.base_revision,
                "current_revision": current_revision,
                "incoming_changes": changes,
                "changed_keys_since_base": sorted(changed_keys),
                "operation_id": payload.operation_id,
                "status": "OPEN",
                "revision": 1,
                "created_by": user.id,
                "created_at": now(),
                "updated_at": now(),
            }
            await database.value.draft_conflicts.insert_one(conflict)
            raise HTTPException(
                status_code=409,
                detail={"code": "DRAFT_CONFLICT_REQUIRES_REVIEW", "conflict_id": conflict["_id"]},
            )
    try:
        if artifact_type == "requirement":
            result = await update_requirement_draft(
                project_id,
                artifact_id,
                RequirementDraftPatch(expected_revision=current_revision, **changes),
                user,
            )
        else:
            result = await update_test_case_draft(
                artifact_id,
                TestCaseDraftPatch(expected_revision=current_revision, **changes),
                project_id,
                user,
            )
    except HTTPException as error:
        if error.status_code != 409:
            raise
        raise HTTPException(status_code=409, detail={"code": "COLLABORATION_RETRY_REQUIRED"}) from error
    record = {
        "_id": new_id("COLOP"),
        "project_id": project_id,
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "operation_id": payload.operation_id,
        "base_revision": payload.base_revision,
        "result_revision": result["meta"]["revision"],
        "changed_keys": sorted(changes),
        "rebased": rebased,
        "result": result,
        "created_by": user.id,
        "created_at": now(),
    }
    try:
        await database.value.collaboration_operations.insert_one(record)
    except DuplicateKeyError:
        existing = await database.value.collaboration_operations.find_one(
            {"project_id": project_id, "operation_id": payload.operation_id}
        )
        if existing:
            return existing["result"]
        raise
    await audit(user.id, "collaboration_operation_applied", "CollaborationSession", record["_id"], project_id, {"artifact_type": artifact_type, "artifact_id": artifact_id, "rebased": rebased})
    return result


@router.post("/du-an/{project_id}/cong-tac/yeu-cau/{artifact_id}/thao-tac")
async def apply_requirement_collaboration_operation(project_id: str, artifact_id: str, payload: CollaborationOperationInput, user: CurrentUser = Depends(get_current_user)):
    return await apply_operation(project_id, "requirement", artifact_id, payload, user)


@router.post("/du-an/{project_id}/cong-tac/ca-kiem-thu/{artifact_id}/thao-tac")
async def apply_test_case_collaboration_operation(project_id: str, artifact_id: str, payload: CollaborationOperationInput, user: CurrentUser = Depends(get_current_user)):
    return await apply_operation(project_id, "test_case", artifact_id, payload, user)


@router.get("/du-an/{project_id}/cong-tac/xung-dot")
async def list_collaboration_conflicts(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "collaboration.conflict.resolve")
    items = await database.value.draft_conflicts.find({"project_id": project_id}).sort("created_at", -1).to_list(1000)
    return envelope(items)


@router.post("/du-an/{project_id}/cong-tac/xung-dot/{conflict_id}/giai-quyet")
async def resolve_collaboration_conflict(project_id: str, conflict_id: str, payload: CollaborationConflictResolution, user: CurrentUser = Depends(get_current_user)):
    conflict = await get_project_entity("draft_conflicts", conflict_id, user, "collaboration.conflict.resolve")
    if conflict["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    current = await artifact_context(project_id, conflict["artifact_type"], conflict["artifact_id"], user, edit=True)
    if current["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": current["revision"]})
    changes = {} if payload.resolution == "KEEP_CURRENT" else conflict["incoming_changes"] if payload.resolution == "APPLY_INCOMING" else payload.merged_changes
    result = None
    if changes:
        result = await apply_operation(project_id, conflict["artifact_type"], conflict["artifact_id"], CollaborationOperationInput(base_revision=current["revision"], operation_id=f"resolve-{conflict_id}-{current['revision']}", changes=changes), user)
    updated = await database.value.draft_conflicts.find_one_and_update({"_id": conflict_id, "project_id": project_id, "status": "OPEN", "revision": conflict["revision"]}, {"$set": {"status": "RESOLVED", "resolution": payload.resolution, "reason": payload.reason, "resolved_by": user.id, "resolved_at": now(), "updated_at": now()}, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "CONFLICT_ALREADY_RESOLVED"})
    await audit(user.id, "collaboration_conflict_resolved", "DraftConflict", conflict_id, project_id, {"resolution": payload.resolution, "reason": payload.reason})
    return envelope({"conflict": updated, "result": result}, revision=updated["revision"])
