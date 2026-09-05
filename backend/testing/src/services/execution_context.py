from fastapi import HTTPException

from src.core.auth import CurrentUser
from src.core.common import get_project_entity


async def resolve_execution_context(
    project_id: str,
    user: CurrentUser,
    *,
    release_id: str | None = None,
    build_id: str | None = None,
    environment_id: str | None = None,
    release: str = "",
    build: str = "",
    environment: str = "",
):
    release_entity = None
    build_entity = None
    environment_entity = None
    if release_id:
        release_entity = await get_project_entity("releases", release_id, user, "release.read")
        if release_entity.get("project_id") != project_id:
            raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
        if release_entity.get("status") == "ARCHIVED":
            raise HTTPException(status_code=422, detail={"code": "RELEASE_ARCHIVED"})
    if build_id:
        build_entity = await get_project_entity("builds", build_id, user, "build.read")
        if build_entity.get("project_id") != project_id:
            raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
        linked_release_id = build_entity.get("release_id")
        if release_id and linked_release_id and linked_release_id != release_id:
            raise HTTPException(status_code=422, detail={"code": "BUILD_RELEASE_MISMATCH"})
        if not release_id and linked_release_id:
            release_id = linked_release_id
            release_entity = await get_project_entity("releases", release_id, user, "release.read")
            if release_entity.get("status") == "ARCHIVED":
                raise HTTPException(status_code=422, detail={"code": "RELEASE_ARCHIVED"})
    if environment_id:
        environment_entity = await get_project_entity(
            "test_environments", environment_id, user, "environment.read"
        )
        if environment_entity.get("project_id") != project_id:
            raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
        if environment_entity.get("status") == "ARCHIVED":
            raise HTTPException(status_code=422, detail={"code": "ENVIRONMENT_ARCHIVED"})
    return {
        "release_id": release_id,
        "build_id": build_id,
        "environment_id": environment_id,
        "release": (release_entity or {}).get("key") or release,
        "build": (build_entity or {}).get("identifier") or build,
        "environment": (environment_entity or {}).get("name") or environment,
    }
