from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now, optimistic_patch
from src.core.database import database
from src.domain.schemas import (
    BuildCreate,
    BuildPatch,
    EnvironmentCreate,
    EnvironmentPatch,
    EnvironmentSecretRefs,
    ReleaseCreate,
    ReleasePatch,
    ReleaseTransition,
)


router = APIRouter(prefix="/kiem-thu", tags=["Ngữ cảnh thực thi kiểm thử"])


def clean_secret_fields(item):
    result = dict(item)
    result.pop("secret_refs", None)
    result["secret_ref_names"] = sorted((item.get("secret_refs") or {}).keys())
    return result


@router.get("/du-an/{project_id}/ban-phat-hanh", openapi_extra={"x-function-ids": ["REL-01"]})
async def list_releases(project_id: str, status: str = Query(default="", max_length=30), user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "release.read")
    query = {"project_id": project_id}
    if status:
        query["status"] = status.upper()
    items = await database.value.releases.find(query).sort("updated_at", -1).to_list(500)
    return envelope(items)


@router.get("/ban-phat-hanh/{release_id}", openapi_extra={"x-function-ids": ["REL-02"]})
async def get_release(release_id: str, user: CurrentUser = Depends(get_current_user)):
    release = await get_project_entity("releases", release_id, user, "release.read")
    return envelope(release, revision=release["revision"])


@router.post("/du-an/{project_id}/ban-phat-hanh", status_code=201, openapi_extra={"x-function-ids": ["REL-03"]})
async def create_release(project_id: str, payload: ReleaseCreate, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "release.create")
    timestamp = now()
    release = {"_id": new_id("REL"), "project_id": project_id, **payload.model_dump(), "status": "PLANNED", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    try:
        await database.value.releases.insert_one(release)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "RELEASE_KEY_EXISTS"})
    await audit(user.id, "release_created", "Release", release["_id"], project_id)
    return envelope(release, revision=1)


@router.patch("/ban-phat-hanh/{release_id}", openapi_extra={"x-function-ids": ["REL-04"]})
async def update_release(release_id: str, payload: ReleasePatch, user: CurrentUser = Depends(get_current_user)):
    release = await get_project_entity("releases", release_id, user, "release.update")
    if release.get("status") not in {"PLANNED", "ACTIVE"}:
        raise HTTPException(status_code=409, detail={"code": "RELEASE_STATE_INVALID"})
    updated = await optimistic_patch("releases", release_id, release["project_id"], payload.expected_revision, payload.model_dump())
    await audit(user.id, "release_updated", "Release", release_id, release["project_id"])
    return envelope(updated, revision=updated["revision"])


async def release_transition(release_id, payload, user, target, permission, action):
    release = await get_project_entity("releases", release_id, user, permission)
    allowed = {"ACTIVE": {"PLANNED"}, "CLOSED": {"ACTIVE"}, "ARCHIVED": {"CLOSED", "PLANNED"}}
    if release.get("status") not in allowed[target]:
        if release.get("status") == target:
            return envelope(release, revision=release["revision"])
        raise HTTPException(status_code=409, detail={"code": "RELEASE_STATE_INVALID", "current_status": release.get("status"), "target_status": target})
    updated = await optimistic_patch("releases", release_id, release["project_id"], payload.expected_revision, {"status": target, f"{target.lower()}_by": user.id, f"{target.lower()}_at": now(), "transition_reason": payload.reason})
    if target == "ACTIVE":
        await database.value.releases.update_many({"project_id": release["project_id"], "_id": {"$ne": release_id}, "status": "ACTIVE"}, {"$set": {"is_current": False}})
        await database.value.releases.update_one({"_id": release_id}, {"$set": {"is_current": True}})
        updated["is_current"] = True
    await audit(user.id, action, "Release", release_id, release["project_id"], {"reason": payload.reason})
    return envelope(updated, revision=updated["revision"])


@router.post("/ban-phat-hanh/{release_id}/kich-hoat", openapi_extra={"x-function-ids": ["REL-05"]})
async def activate_release(release_id: str, payload: ReleaseTransition, user: CurrentUser = Depends(get_current_user)):
    return await release_transition(release_id, payload, user, "ACTIVE", "release.manage", "release_activated")


@router.post("/ban-phat-hanh/{release_id}/dong", openapi_extra={"x-function-ids": ["REL-06"]})
async def close_release(release_id: str, payload: ReleaseTransition, user: CurrentUser = Depends(get_current_user)):
    return await release_transition(release_id, payload, user, "CLOSED", "release.close", "release_closed")


@router.post("/ban-phat-hanh/{release_id}/luu-tru", openapi_extra={"x-function-ids": ["REL-07"]})
async def archive_release(release_id: str, payload: ReleaseTransition, user: CurrentUser = Depends(get_current_user)):
    return await release_transition(release_id, payload, user, "ARCHIVED", "release.archive", "release_archived")


@router.get("/du-an/{project_id}/ban-dung", openapi_extra={"x-function-ids": ["BLD-01"]})
async def list_builds(project_id: str, release_id: str = Query(default="", max_length=200), user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "build.read")
    query = {"project_id": project_id}
    if release_id:
        query["release_id"] = release_id
    items = await database.value.builds.find(query).sort("created_at", -1).to_list(500)
    return envelope(items)


@router.get("/ban-dung/{build_id}", openapi_extra={"x-function-ids": ["BLD-01"]})
async def get_build(build_id: str, user: CurrentUser = Depends(get_current_user)):
    build = await get_project_entity("builds", build_id, user, "build.read")
    return envelope(build, revision=build["revision"])


@router.post("/du-an/{project_id}/ban-dung", status_code=201, openapi_extra={"x-function-ids": ["BLD-02"]})
async def create_build(project_id: str, payload: BuildCreate, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "build.create")
    timestamp = now()
    build = {"_id": new_id("BLD"), "project_id": project_id, **payload.model_dump(), "status": "ACTIVE", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    try:
        await database.value.builds.insert_one(build)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "BUILD_IDENTIFIER_EXISTS"})
    await audit(user.id, "build_created", "Build", build["_id"], project_id)
    return envelope(build, revision=1)


@router.patch("/ban-dung/{build_id}", openapi_extra={"x-function-ids": ["BLD-02"]})
async def update_build(build_id: str, payload: BuildPatch, user: CurrentUser = Depends(get_current_user)):
    build = await get_project_entity("builds", build_id, user, "build.manage")
    updated = await optimistic_patch("builds", build_id, build["project_id"], payload.expected_revision, payload.model_dump())
    await audit(user.id, "build_updated", "Build", build_id, build["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/ban-dung/{build_id}/dat-hien-tai", openapi_extra={"x-function-ids": ["BLD-03"]})
async def set_current_build(build_id: str, payload: ReleaseTransition, user: CurrentUser = Depends(get_current_user)):
    build = await get_project_entity("builds", build_id, user, "build.manage")
    updated = await optimistic_patch("builds", build_id, build["project_id"], payload.expected_revision, {"is_current": True})
    await database.value.builds.update_many({"project_id": build["project_id"], "_id": {"$ne": build_id}}, {"$set": {"is_current": False}})
    await audit(user.id, "build_set_current", "Build", build_id, build["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.get("/du-an/{project_id}/moi-truong", openapi_extra={"x-function-ids": ["ENV-01"]})
async def list_environments(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "environment.read")
    items = await database.value.test_environments.find({"project_id": project_id, "status": {"$ne": "ARCHIVED"}}).sort("updated_at", -1).to_list(500)
    return envelope([clean_secret_fields(item) for item in items])


@router.get("/moi-truong/{environment_id}", openapi_extra={"x-function-ids": ["ENV-01"]})
async def get_environment(environment_id: str, user: CurrentUser = Depends(get_current_user)):
    environment = await get_project_entity("test_environments", environment_id, user, "environment.read")
    return envelope(clean_secret_fields(environment), revision=environment["revision"])


@router.post("/du-an/{project_id}/moi-truong", status_code=201, openapi_extra={"x-function-ids": ["ENV-02"]})
async def create_environment(project_id: str, payload: EnvironmentCreate, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "environment.create")
    timestamp = now()
    environment = {"_id": new_id("ENV"), "project_id": project_id, **payload.model_dump(), "status": "ACTIVE", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    try:
        await database.value.test_environments.insert_one(environment)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "ENVIRONMENT_NAME_EXISTS"})
    await audit(user.id, "environment_created", "TestEnvironment", environment["_id"], project_id)
    return envelope(clean_secret_fields(environment), revision=1)


@router.patch("/moi-truong/{environment_id}", openapi_extra={"x-function-ids": ["ENV-03"]})
async def update_environment(environment_id: str, payload: EnvironmentPatch, user: CurrentUser = Depends(get_current_user)):
    environment = await get_project_entity("test_environments", environment_id, user, "environment.update")
    updated = await optimistic_patch("test_environments", environment_id, environment["project_id"], payload.expected_revision, payload.model_dump())
    await audit(user.id, "environment_updated", "TestEnvironment", environment_id, environment["project_id"])
    return envelope(clean_secret_fields(updated), revision=updated["revision"])


@router.patch("/moi-truong/{environment_id}/bi-mat", openapi_extra={"x-function-ids": ["ENV-04"]})
async def update_environment_secrets(environment_id: str, payload: EnvironmentSecretRefs, user: CurrentUser = Depends(get_current_user)):
    environment = await get_project_entity("test_environments", environment_id, user, "environment.secret_ref.manage")
    updated = await optimistic_patch("test_environments", environment_id, environment["project_id"], payload.expected_revision, {"secret_refs": payload.secret_refs})
    await audit(user.id, "environment_secret_refs_updated", "TestEnvironment", environment_id, environment["project_id"], {"names": sorted(payload.secret_refs)})
    return envelope(clean_secret_fields(updated), revision=updated["revision"])


@router.post("/moi-truong/{environment_id}/luu-tru", openapi_extra={"x-function-ids": ["ENV-05"]})
async def archive_environment(environment_id: str, payload: ReleaseTransition, user: CurrentUser = Depends(get_current_user)):
    environment = await get_project_entity("test_environments", environment_id, user, "environment.archive")
    updated = await optimistic_patch("test_environments", environment_id, environment["project_id"], payload.expected_revision, {"status": "ARCHIVED", "archive_reason": payload.reason, "archived_at": now(), "archived_by": user.id})
    await audit(user.id, "environment_archived", "TestEnvironment", environment_id, environment["project_id"], {"reason": payload.reason})
    return envelope(clean_secret_fields(updated), revision=updated["revision"])
