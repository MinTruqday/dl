from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.domain.schemas import DataSetCreate, DataSetVersionCreate


router = APIRouter(prefix="/kiem-thu", tags=["QA Test Data"])


@router.post("/du-an/{project_id}/bo-du-lieu", status_code=201)
async def create_data_set(
    project_id: str,
    payload: DataSetCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.create")
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
    return envelope({**data_set, "current_version": version}, revision=1)


@router.get("/du-an/{project_id}/bo-du-lieu")
async def list_data_sets(
    project_id: str,
    q: str = Query(default="", max_length=300),
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.read")
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
        [{**item, "current_version": by_id.get(item["current_version_id"])} for item in items]
    )


@router.get("/bo-du-lieu/{data_set_id}")
async def get_data_set(
    data_set_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    data_set = await get_project_entity("data_sets", data_set_id, user, "testcase.read")
    version = await database.value.data_set_versions.find_one(
        {
            "_id": data_set["current_version_id"],
            "project_id": data_set["project_id"],
            "data_set_id": data_set_id,
        }
    )
    return envelope({**data_set, "current_version": version}, revision=data_set["revision"])


@router.get("/bo-du-lieu/{data_set_id}/phien-ban")
async def list_data_set_versions(
    data_set_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    data_set = await get_project_entity("data_sets", data_set_id, user, "testcase.read")
    versions = await database.value.data_set_versions.find(
        {"project_id": data_set["project_id"], "data_set_id": data_set_id}
    ).sort("version", -1).to_list(500)
    return envelope(versions)


@router.post("/bo-du-lieu/{data_set_id}/phien-ban", status_code=201)
async def create_data_set_version(
    data_set_id: str,
    payload: DataSetVersionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    data_set = await get_project_entity("data_sets", data_set_id, user, "testcase.update")
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
    return envelope(version, revision=data_set["revision"] + 1)
