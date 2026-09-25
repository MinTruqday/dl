from fastapi import HTTPException

from src.core.common import audit, get_project_entity, now
from src.repositories.requirement_analysis import requirement_analysis_repository
from src.services.domain_policy import domain_policy


DEPENDENCY_POLICY = domain_policy("requirement_dependency")


async def dependency_reaches(start_id, target_id, project_id):
    pending = [start_id]
    visited = set()
    while pending:
        current_id = pending.pop()
        if current_id == target_id:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        requirement = await requirement_analysis_repository.find_requirement(
            current_id, project_id, {"current_version_id": 1}
        )
        if not requirement:
            continue
        version = await requirement_analysis_repository.find_version(
            requirement.get("current_version_id"),
            project_id,
            {"dependencies": 1},
        )
        pending.extend((version or {}).get("dependencies", []))
    return False


async def add_dependency(requirement_id, dependency_id, expected_revision, user):
    requirement = await get_project_entity(
        DEPENDENCY_POLICY["requirement_collection"],
        requirement_id,
        user,
        DEPENDENCY_POLICY["manage_permission"],
    )
    if dependency_id == requirement_id:
        raise HTTPException(status_code=422, detail={"code": DEPENDENCY_POLICY["cycle_code"]})
    dependency = await requirement_analysis_repository.find_requirement(
        dependency_id, requirement["project_id"]
    )
    if not dependency:
        raise HTTPException(
            status_code=422,
            detail={"code": DEPENDENCY_POLICY["invalid_dependency_code"]},
        )
    version = await requirement_analysis_repository.find_version(
        requirement["current_version_id"], requirement["project_id"]
    )
    if not version or version.get("status") != DEPENDENCY_POLICY["draft_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": DEPENDENCY_POLICY["immutable_version_code"]},
        )
    if version.get("revision") != expected_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": DEPENDENCY_POLICY["revision_conflict_code"],
                "current_revision": version.get("revision"),
            },
        )
    dependencies = list(dict.fromkeys(version.get("dependencies", [])))
    if dependency_id in dependencies:
        return version
    if await dependency_reaches(dependency_id, requirement_id, requirement["project_id"]):
        raise HTTPException(status_code=422, detail={"code": DEPENDENCY_POLICY["cycle_code"]})
    dependencies.append(dependency_id)
    updated = await requirement_analysis_repository.update_draft_dependencies(
        version["_id"],
        requirement["project_id"],
        expected_revision,
        dependencies,
        now(),
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": DEPENDENCY_POLICY["revision_conflict_code"]},
        )
    await audit(
        user.id,
        DEPENDENCY_POLICY["added_event"],
        DEPENDENCY_POLICY["entity"],
        requirement_id,
        requirement["project_id"],
        {"dependency_requirement_id": dependency_id},
    )
    return updated


async def remove_dependency(requirement_id, dependency_id, expected_revision, user):
    requirement = await get_project_entity(
        DEPENDENCY_POLICY["requirement_collection"],
        requirement_id,
        user,
        DEPENDENCY_POLICY["manage_permission"],
    )
    version = await requirement_analysis_repository.find_version(
        requirement["current_version_id"], requirement["project_id"]
    )
    if not version or version.get("status") != DEPENDENCY_POLICY["draft_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": DEPENDENCY_POLICY["immutable_version_code"]},
        )
    dependencies = list(dict.fromkeys(version.get("dependencies", [])))
    if dependency_id not in dependencies:
        return version
    updated = await requirement_analysis_repository.update_draft_dependencies(
        version["_id"],
        requirement["project_id"],
        expected_revision,
        [item for item in dependencies if item != dependency_id],
        now(),
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": DEPENDENCY_POLICY["revision_conflict_code"]},
        )
    await audit(
        user.id,
        DEPENDENCY_POLICY["removed_event"],
        DEPENDENCY_POLICY["entity"],
        requirement_id,
        requirement["project_id"],
        {"dependency_requirement_id": dependency_id},
    )
    return updated
