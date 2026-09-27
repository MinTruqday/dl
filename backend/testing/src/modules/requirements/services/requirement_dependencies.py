from fastapi import HTTPException

from src.core.common import audit, get_project_entity, now
from src.repositories.requirement_analysis import requirement_analysis_repository





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
        'requirements',
        requirement_id,
        user,
        'requirement_dependency.manage',
    )
    if dependency_id == requirement_id:
        raise HTTPException(status_code=422, detail={"code": 'REQUIREMENT_DEPENDENCY_CYCLE'})
    dependency = await requirement_analysis_repository.find_requirement(
        dependency_id, requirement["project_id"]
    )
    if not dependency:
        raise HTTPException(
            status_code=422,
            detail={"code": 'INVALID_REQUIREMENT_DEPENDENCY'},
        )
    version = await requirement_analysis_repository.find_version(
        requirement["current_version_id"], requirement["project_id"]
    )
    if not version or version.get("status") != 'DRAFT':
        raise HTTPException(
            status_code=409,
            detail={"code": 'IMMUTABLE_REQUIREMENT_VERSION'},
        )
    if version.get("revision") != expected_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": 'REVISION_CONFLICT',
                "current_revision": version.get("revision"),
            },
        )
    dependencies = list(dict.fromkeys(version.get("dependencies", [])))
    if dependency_id in dependencies:
        return version
    if await dependency_reaches(dependency_id, requirement_id, requirement["project_id"]):
        raise HTTPException(status_code=422, detail={"code": 'REQUIREMENT_DEPENDENCY_CYCLE'})
    dependencies.append(dependency_id)
    updated = await requirement_analysis_repository.update_draft_dependencies(
        version["_id"],
        requirement["project_id"],
        expected_revision,
        'DRAFT',
        dependencies,
        now(),
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": 'REVISION_CONFLICT'},
        )
    await audit(
        user.id,
        'requirement_dependency_added',
        'Requirement',
        requirement_id,
        requirement["project_id"],
        {"dependency_requirement_id": dependency_id},
    )
    return updated


async def remove_dependency(requirement_id, dependency_id, expected_revision, user):
    requirement = await get_project_entity(
        'requirements',
        requirement_id,
        user,
        'requirement_dependency.manage',
    )
    version = await requirement_analysis_repository.find_version(
        requirement["current_version_id"], requirement["project_id"]
    )
    if not version or version.get("status") != 'DRAFT':
        raise HTTPException(
            status_code=409,
            detail={"code": 'IMMUTABLE_REQUIREMENT_VERSION'},
        )
    dependencies = list(dict.fromkeys(version.get("dependencies", [])))
    if dependency_id not in dependencies:
        return version
    updated = await requirement_analysis_repository.update_draft_dependencies(
        version["_id"],
        requirement["project_id"],
        expected_revision,
        'DRAFT',
        [item for item in dependencies if item != dependency_id],
        now(),
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": 'REVISION_CONFLICT'},
        )
    await audit(
        user.id,
        'requirement_dependency_removed',
        'Requirement',
        requirement_id,
        requirement["project_id"],
        {"dependency_requirement_id": dependency_id},
    )
    return updated
