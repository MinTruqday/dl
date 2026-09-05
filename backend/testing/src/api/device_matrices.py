from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now, optimistic_patch
from src.core.database import database
from src.domain.schemas import (
    DeviceMatrixArchive,
    DeviceMatrixAssignment,
    DeviceMatrixCreate,
    DeviceMatrixPatch,
)


router = APIRouter(prefix="/kiem-thu", tags=["Ma trận thiết bị"])


@router.get(
    "/du-an/{project_id}/ma-tran-thiet-bi",
    openapi_extra={"x-function-ids": ["DEVMTX-01"]},
)
async def list_device_matrices(
    project_id: str,
    include_archived: bool = Query(default=False),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "device_matrix.read")
    query = {"project_id": project_id}
    if not include_archived:
        query["status"] = {"$ne": "ARCHIVED"}
    items = await database.value.device_matrices.find(query).sort("updated_at", -1).to_list(500)
    return envelope(items)


@router.get(
    "/ma-tran-thiet-bi/{matrix_id}",
    openapi_extra={"x-function-ids": ["DEVMTX-01"]},
)
async def get_device_matrix(
    matrix_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    matrix = await get_project_entity(
        "device_matrices", matrix_id, user, "device_matrix.read"
    )
    return envelope(matrix, revision=matrix["revision"])


@router.post(
    "/du-an/{project_id}/ma-tran-thiet-bi",
    status_code=201,
    openapi_extra={"x-function-ids": ["DEVMTX-02"]},
)
async def create_device_matrix(
    project_id: str,
    payload: DeviceMatrixCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "device_matrix.manage")
    timestamp = now()
    matrix = {
        "_id": new_id("DMX"),
        "project_id": project_id,
        **payload.model_dump(),
        "status": "ACTIVE",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.device_matrices.insert_one(matrix)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "DEVICE_MATRIX_NAME_EXISTS"})
    await audit(user.id, "device_matrix_created", "DeviceMatrix", matrix["_id"], project_id)
    return envelope(matrix, revision=1)


@router.patch(
    "/ma-tran-thiet-bi/{matrix_id}",
    openapi_extra={"x-function-ids": ["DEVMTX-02"]},
)
async def update_device_matrix(
    matrix_id: str,
    payload: DeviceMatrixPatch,
    user: CurrentUser = Depends(get_current_user),
):
    matrix = await get_project_entity(
        "device_matrices", matrix_id, user, "device_matrix.manage"
    )
    if matrix.get("status") != "ACTIVE":
        raise HTTPException(status_code=409, detail={"code": "DEVICE_MATRIX_ARCHIVED"})
    try:
        updated = await optimistic_patch(
            "device_matrices",
            matrix_id,
            matrix["project_id"],
            payload.expected_revision,
            payload.model_dump(exclude_unset=True),
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "DEVICE_MATRIX_NAME_EXISTS"})
    await audit(
        user.id,
        "device_matrix_updated",
        "DeviceMatrix",
        matrix_id,
        matrix["project_id"],
    )
    return envelope(updated, revision=updated["revision"])


@router.post(
    "/ma-tran-thiet-bi/{matrix_id}/luu-tru",
    openapi_extra={"x-function-ids": ["DEVMTX-02"]},
)
async def archive_device_matrix(
    matrix_id: str,
    payload: DeviceMatrixArchive,
    user: CurrentUser = Depends(get_current_user),
):
    matrix = await get_project_entity(
        "device_matrices", matrix_id, user, "device_matrix.manage"
    )
    if matrix.get("status") == "ARCHIVED":
        return envelope(matrix, revision=matrix["revision"])
    updated = await optimistic_patch(
        "device_matrices",
        matrix_id,
        matrix["project_id"],
        payload.expected_revision,
        {
            "status": "ARCHIVED",
            "archive_reason": payload.reason,
            "archived_by": user.id,
            "archived_at": now(),
        },
    )
    await audit(
        user.id,
        "device_matrix_archived",
        "DeviceMatrix",
        matrix_id,
        matrix["project_id"],
        {"reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])


@router.post(
    "/ma-tran-thiet-bi/{matrix_id}/gan",
    openapi_extra={"x-function-ids": ["DEVMTX-03"]},
)
async def assign_device_matrix(
    matrix_id: str,
    payload: DeviceMatrixAssignment,
    user: CurrentUser = Depends(get_current_user),
):
    matrix = await get_project_entity(
        "device_matrices", matrix_id, user, "device_matrix.assign"
    )
    if matrix.get("status") != "ACTIVE":
        raise HTTPException(status_code=409, detail={"code": "DEVICE_MATRIX_ARCHIVED"})
    enabled_profiles = {
        item["key"]: item for item in matrix.get("profiles", []) if item.get("enabled", True)
    }
    selected_keys = list(dict.fromkeys(payload.profile_keys or enabled_profiles.keys()))
    if not selected_keys or not set(selected_keys) <= set(enabled_profiles):
        raise HTTPException(status_code=422, detail={"code": "DEVICE_PROFILE_SELECTION_INVALID"})
    collection = "test_plans" if payload.target_type == "test_plan" else "test_runs"
    target = await get_project_entity(collection, payload.target_id, user, "device_matrix.assign")
    if target["project_id"] != matrix["project_id"]:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if target.get("status") != "DRAFT":
        raise HTTPException(
            status_code=409,
            detail={"code": "DEVICE_MATRIX_TARGET_SCOPE_FROZEN"},
        )
    snapshot = {
        "matrix_id": matrix_id,
        "matrix_name": matrix["name"],
        "matrix_revision": matrix["revision"],
        "profile_keys": selected_keys,
        "profiles": [enabled_profiles[key] for key in selected_keys],
        "captured_at": now(),
    }
    updated = await optimistic_patch(
        collection,
        payload.target_id,
        matrix["project_id"],
        payload.expected_target_revision,
        {
            "device_matrix_id": matrix_id,
            "device_profile_keys": selected_keys,
            "device_matrix_snapshot": snapshot,
        },
    )
    await audit(
        user.id,
        "device_matrix_assigned",
        "TestPlan" if payload.target_type == "test_plan" else "TestRun",
        payload.target_id,
        matrix["project_id"],
        {
            "device_matrix_id": matrix_id,
            "matrix_revision": matrix["revision"],
            "profile_keys": selected_keys,
        },
    )
    return envelope(updated, revision=updated["revision"])
