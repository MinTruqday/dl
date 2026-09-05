from itertools import product
from math import prod

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.domain.schemas import (
    DataSetArchive,
    DataSetBind,
    DataSetCreate,
    DataSetPreview,
    DataSetVersionCreate,
)


router = APIRouter(prefix="/kiem-thu", tags=["Dữ liệu kiểm thử"])


@router.post(
    "/du-an/{project_id}/du-lieu-kiem-thu",
    status_code=201,
    openapi_extra={"x-function-ids": ["DATA-02"]},
)
async def create_data_set(
    project_id: str,
    payload: DataSetCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testdata.create")
    timestamp = now()
    data_set_id = new_id("DATA")
    version = {
        "_id": new_id("DATAV"),
        "project_id": project_id,
        "data_set_id": data_set_id,
        "version": 1,
        **payload.model_dump(),
        "change_reason": "Tạo bộ dữ liệu kiểm thử",
        "created_by": user.id,
        "created_at": timestamp,
    }
    data_set = {
        "_id": data_set_id,
        "project_id": project_id,
        "name": payload.name,
        "current_version_id": version["_id"],
        "revision": 1,
        "status": "ACTIVE",
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.data_set_versions.insert_one(version)
        await database.value.data_sets.insert_one(data_set)
    except DuplicateKeyError:
        await database.value.data_set_versions.delete_one(
            {"_id": version["_id"], "project_id": project_id}
        )
        raise HTTPException(status_code=409, detail={"code": "DATA_SET_NAME_EXISTS"})
    await audit(user.id, "data_set_created", "DataSet", data_set_id, project_id)
    return envelope(
        {**data_set, "current_version": public_data_set_version(version)}, revision=1
    )


@router.get(
    "/du-an/{project_id}/du-lieu-kiem-thu",
    openapi_extra={"x-function-ids": ["DATA-01"]},
)
async def list_data_sets(
    project_id: str,
    q: str = Query(default="", max_length=300),
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testdata.read")
    query = {"project_id": project_id, "status": "ACTIVE"}
    if q:
        query["name"] = {"$regex": q, "$options": "i"}
    items = await database.value.data_sets.find(query).sort("updated_at", -1).to_list(limit)
    version_ids = [item["current_version_id"] for item in items]
    versions = await database.value.data_set_versions.find(
        {"project_id": project_id, "_id": {"$in": version_ids}}
    ).to_list(limit)
    by_id = {item["_id"]: item for item in versions}
    return envelope(
        [
            {
                **item,
                "current_version": public_data_set_version(
                    by_id.get(item["current_version_id"])
                ),
            }
            for item in items
        ]
    )


@router.get("/du-lieu-kiem-thu/{data_set_id}", openapi_extra={"x-function-ids": ["DATA-01"]})
async def get_data_set(
    data_set_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    data_set = await get_project_entity("data_sets", data_set_id, user, "testdata.read")
    version = await database.value.data_set_versions.find_one(
        {
            "_id": data_set["current_version_id"],
            "project_id": data_set["project_id"],
            "data_set_id": data_set_id,
        }
    )
    return envelope(
        {**data_set, "current_version": public_data_set_version(version)},
        revision=data_set["revision"],
    )


@router.get(
    "/du-lieu-kiem-thu/{data_set_id}/phien-ban",
    openapi_extra={"x-function-ids": ["DATA-01"]},
)
async def list_data_set_versions(
    data_set_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    data_set = await get_project_entity("data_sets", data_set_id, user, "testdata.read")
    versions = await database.value.data_set_versions.find(
        {"project_id": data_set["project_id"], "data_set_id": data_set_id}
    ).sort("version", -1).to_list(500)
    return envelope([public_data_set_version(version) for version in versions])


@router.post(
    "/du-lieu-kiem-thu/{data_set_id}/phien-ban",
    status_code=201,
    openapi_extra={"x-function-ids": ["DATA-03"]},
)
async def create_data_set_version(
    data_set_id: str,
    payload: DataSetVersionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    data_set = await get_project_entity("data_sets", data_set_id, user, "testdata.update")
    if data_set.get("current_version_id") != payload.expected_current_version_id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "REVISION_CONFLICT",
                "current_version_id": data_set.get("current_version_id"),
            },
        )
    current = await database.value.data_set_versions.find_one(
        {
            "_id": payload.expected_current_version_id,
            "project_id": data_set["project_id"],
            "data_set_id": data_set_id,
        }
    )
    if not current:
        raise HTTPException(status_code=409, detail={"code": "DATA_SET_HISTORY_INVALID"})
    timestamp = now()
    version = {
        "_id": new_id("DATAV"),
        "project_id": data_set["project_id"],
        "data_set_id": data_set_id,
        "version": int(current["version"]) + 1,
        "name": payload.name,
        "variables": payload.variables,
        "secret_refs": payload.secret_refs,
        "change_reason": payload.change_reason,
        "parent_version_id": current["_id"],
        "created_by": user.id,
        "created_at": timestamp,
    }
    try:
        await database.value.data_set_versions.insert_one(version)
        updated = await database.value.data_sets.update_one(
            {
                "_id": data_set_id,
                "project_id": data_set["project_id"],
                "current_version_id": current["_id"],
                "revision": data_set["revision"],
            },
            {
                "$set": {
                    "name": payload.name,
                    "current_version_id": version["_id"],
                    "updated_at": timestamp,
                },
                "$inc": {"revision": 1},
            },
        )
        if updated.matched_count != 1:
            raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    except DuplicateKeyError as error:
        await database.value.data_set_versions.delete_one(
            {"_id": version["_id"], "project_id": data_set["project_id"]}
        )
        raise HTTPException(status_code=409, detail={"code": "DATA_SET_VERSION_CONFLICT"}) from error
    except Exception:
        await database.value.data_set_versions.delete_one(
            {"_id": version["_id"], "project_id": data_set["project_id"]}
        )
        raise
    await audit(
        user.id,
        "data_set_version_created",
        "DataSetVersion",
        version["_id"],
        data_set["project_id"],
        {"data_set_id": data_set_id, "version": version["version"]},
    )
    return envelope(
        public_data_set_version(version), revision=data_set["revision"] + 1
    )


def public_data_set_version(version):
    if not version:
        return None
    return {
        **version,
        "variable_names": sorted((version.get("variables") or {}).keys()),
        "secret_names": sorted((version.get("secret_refs") or {}).keys()),
        "secret_refs": {
            key: "[BÍ MẬT]" for key in sorted((version.get("secret_refs") or {}).keys())
        },
    }


def expand_variables(variables, max_rows):
    keys = sorted(variables)
    choices = []
    for key in keys:
        value = variables[key]
        values = value if isinstance(value, list) else [value]
        choices.append(values[:max_rows])
    total = prod(len(values) for values in choices) if choices else 1
    rows = []
    combinations = product(*choices) if choices else [()]
    for combination in combinations:
        rows.append(dict(zip(keys, combination)))
        if len(rows) >= max_rows:
            break
    return rows, total > max_rows


async def _get_data_set_version(data_set_id, version_id, user, permission="testdata.read"):
    data_set = await get_project_entity("data_sets", data_set_id, user, permission)
    version = await database.value.data_set_versions.find_one(
        {"_id": version_id, "project_id": data_set["project_id"], "data_set_id": data_set_id}
    )
    if not version:
        raise HTTPException(status_code=404, detail={"code": "DATA_SET_VERSION_NOT_FOUND"})
    return data_set, version


@router.post(
    "/du-an/{project_id}/du-lieu-kiem-thu/{data_set_id}/gan-ca-kiem-thu",
    openapi_extra={"x-function-ids": ["DATA-04"]},
)
async def bind_data_set(
    project_id: str,
    data_set_id: str,
    payload: DataSetBind,
    user: CurrentUser = Depends(get_current_user),
):
    data_set, version = await _get_data_set_version(
        data_set_id, payload.data_set_version_id, user, "testdata.bind"
    )
    if data_set["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    draft = await get_project_entity(
        "test_case_drafts", payload.test_case_draft_id, user, "testdata.bind"
    )
    if draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if draft.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "TEST_CASE_DRAFT_IMMUTABLE"})
    updated = await database.value.test_case_drafts.find_one_and_update(
        {
            "_id": draft["_id"],
            "project_id": project_id,
            "status": "DRAFT",
            "revision": payload.expected_revision,
        },
        {
            "$addToSet": {"data_set_version_ids": version["_id"]},
            "$inc": {"revision": 1},
            "$set": {"updated_at": now()},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "data_set_bound",
        "DataSetVersion",
        version["_id"],
        project_id,
        {"test_case_draft_id": draft["_id"]},
    )
    return envelope(updated, revision=updated["revision"])


@router.post(
    "/du-an/{project_id}/du-lieu-kiem-thu/{data_set_id}/xem-truoc",
    openapi_extra={"x-function-ids": ["DATA-05"]},
)
async def preview_data_set(
    project_id: str,
    data_set_id: str,
    payload: DataSetPreview,
    user: CurrentUser = Depends(get_current_user),
):
    data_set, version = await _get_data_set_version(data_set_id, payload.data_set_version_id, user)
    if data_set["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    rows, truncated = expand_variables(version.get("variables") or {}, payload.max_rows)
    return envelope(
        {
            "data_set_id": data_set_id,
            "data_set_version_id": version["_id"],
            "items": rows,
            "secret_names": sorted((version.get("secret_refs") or {}).keys()),
            "truncated": truncated,
        }
    )


@router.post(
    "/du-an/{project_id}/du-lieu-kiem-thu/{data_set_id}/luu-tru",
    openapi_extra={"x-function-ids": ["DATA-06"]},
)
async def archive_data_set(
    project_id: str,
    data_set_id: str,
    payload: DataSetArchive,
    user: CurrentUser = Depends(get_current_user),
):
    data_set = await get_project_entity("data_sets", data_set_id, user, "testdata.archive")
    if data_set["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if data_set.get("status") == "ARCHIVED":
        return envelope(data_set, revision=data_set.get("revision", 1))
    updated = await database.value.data_sets.find_one_and_update(
        {
            "_id": data_set_id,
            "project_id": project_id,
            "status": "ACTIVE",
            "revision": payload.expected_revision,
        },
        {
            "$set": {
                "status": "ARCHIVED",
                "archive_reason": payload.reason,
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "data_set_archived",
        "DataSet",
        data_set_id,
        project_id,
        {"reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])
