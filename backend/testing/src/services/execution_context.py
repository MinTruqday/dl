from fastapi import HTTPException

from src.core.auth import CurrentUser
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, new_id, now, optimistic_patch
from src.repositories import execution_context_repository
from src.services.domain_policy import domain_policy


CONTEXT_POLICY = domain_policy("execution_context")


async def ensure_release_completion_gate(project_id: str, release_id: str):
    policy = CONTEXT_POLICY
    project = await execution_context_repository.project_settings(project_id)
    if (
        not (project or {})
        .get("settings", {})
        .get(policy["completion_gate_setting"], policy["completion_gate_default"])
    ):
        return False
    if not await execution_context_repository.approved_completion_exists(
        project_id, release_id, policy["completion_approved_statuses"]
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["completion_gate_failed"]},
        )
    return True


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
    policy = CONTEXT_POLICY
    collections = policy["collections"]
    permissions = policy["permissions"]
    codes = policy["error_codes"]
    archived_status = policy["statuses"]["archived"]
    release_entity = None
    build_entity = None
    environment_entity = None
    if release_id:
        release_entity = await get_project_entity(
            collections["release"], release_id, user, permissions["release_read"]
        )
        if release_entity.get("project_id") != project_id:
            raise HTTPException(status_code=422, detail={"code": codes["project_mismatch"]})
        if release_entity.get("status") == archived_status:
            raise HTTPException(status_code=422, detail={"code": codes["release_archived"]})
    if build_id:
        build_entity = await get_project_entity(
            collections["build"], build_id, user, permissions["build_read"]
        )
        if build_entity.get("project_id") != project_id:
            raise HTTPException(status_code=422, detail={"code": codes["project_mismatch"]})
        linked_release_id = build_entity.get("release_id")
        if release_id and linked_release_id and linked_release_id != release_id:
            raise HTTPException(status_code=422, detail={"code": codes["build_release_mismatch"]})
        if not release_id and linked_release_id:
            release_id = linked_release_id
            release_entity = await get_project_entity(
                collections["release"], release_id, user, permissions["release_read"]
            )
            if release_entity.get("status") == archived_status:
                raise HTTPException(status_code=422, detail={"code": codes["release_archived"]})
    if environment_id:
        environment_entity = await get_project_entity(
            collections["environment"],
            environment_id,
            user,
            permissions["environment_read"],
        )
        if environment_entity.get("project_id") != project_id:
            raise HTTPException(status_code=422, detail={"code": codes["project_mismatch"]})
        if environment_entity.get("status") == archived_status:
            raise HTTPException(status_code=422, detail={"code": codes["environment_archived"]})
    return {
        "release_id": release_id,
        "build_id": build_id,
        "environment_id": environment_id,
        "release": (release_entity or {}).get("key") or release,
        "build": (build_entity or {}).get("identifier") or build,
        "environment": (environment_entity or {}).get("name") or environment,
    }


def clean_secret_fields(item):
    result = dict(item)
    result.pop("secret_refs", None)
    result["secret_ref_names"] = sorted((item.get("secret_refs") or {}).keys())
    return result


class ExecutionContextService:
    @staticmethod
    async def list_releases(project_id, status, user):
        await get_project(
            project_id, user, CONTEXT_POLICY["permissions"]["release_read"]
        )
        query = {"project_id": project_id}
        if status:
            query["status"] = status.upper()
        return await execution_context_repository.list_releases(query)

    @staticmethod
    async def get_release(release_id, user):
        policy = CONTEXT_POLICY
        return await get_project_entity(
            policy["collections"]["release"],
            release_id,
            user,
            policy["permissions"]["release_read"],
        )

    @staticmethod
    async def create_release(project_id, payload, user):
        policy = CONTEXT_POLICY
        await get_project(project_id, user, policy["permissions"]["release_create"])
        timestamp = now()
        release = {
            "_id": new_id(policy["id_prefixes"]["release"]),
            "project_id": project_id,
            **payload.model_dump(),
            "status": policy["statuses"]["planned"],
            "revision": policy["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await execution_context_repository.insert_release(release)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["release_key_exists"]},
            )
        await audit(
            user.id,
            policy["events"]["release_created"],
            policy["entity_types"]["release"],
            release["_id"],
            project_id,
        )
        return release

    @staticmethod
    async def update_release(release_id, payload, user):
        policy = CONTEXT_POLICY
        release = await get_project_entity(
            policy["collections"]["release"],
            release_id,
            user,
            policy["permissions"]["release_update"],
        )
        if release.get("status") not in set(policy["release_editable_statuses"]):
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["release_state_invalid"]},
            )
        updated = await optimistic_patch(
            policy["collections"]["release"],
            release_id,
            release["project_id"],
            payload.expected_revision,
            payload.model_dump(),
        )
        await audit(
            user.id,
            policy["events"]["release_updated"],
            policy["entity_types"]["release"],
            release_id,
            release["project_id"],
        )
        return updated

    @staticmethod
    async def transition_release(release_id, payload, user, transition_action):
        policy = CONTEXT_POLICY
        transition = policy["release_transitions"][transition_action]
        target = transition["target"]
        release = await get_project_entity(
            policy["collections"]["release"],
            release_id,
            user,
            transition["permission"],
        )
        if release.get("status") not in set(transition["sources"]):
            if release.get("status") == target:
                return release
            raise HTTPException(
                status_code=409,
                detail={
                    "code": policy["error_codes"]["release_state_invalid"],
                    "current_status": release.get("status"),
                    "target_status": target,
                },
            )
        completion_gate_applied = False
        if target == policy["statuses"]["closed"]:
            try:
                completion_gate_applied = await ensure_release_completion_gate(release["project_id"], release_id)
            except HTTPException:
                await audit(
                    user.id,
                    policy["events"]["release_close_blocked"],
                    policy["entity_types"]["release"],
                    release_id,
                    release["project_id"],
                    {"reason": payload.reason},
                )
                raise
        updated = await optimistic_patch(
            policy["collections"]["release"],
            release_id,
            release["project_id"],
            payload.expected_revision,
            {
                "status": target,
                f"{target.lower()}_by": user.id,
                f"{target.lower()}_at": now(),
                "transition_reason": payload.reason,
            },
        )
        if target == policy["statuses"]["active"]:
            await execution_context_repository.set_current_release(
                release["project_id"], release_id, policy["statuses"]["active"]
            )
            updated["is_current"] = True
        event = (
            policy["events"]["release_closed_after_completion"]
            if completion_gate_applied
            else transition["event"]
        )
        await audit(
            user.id,
            event,
            policy["entity_types"]["release"],
            release_id,
            release["project_id"],
            {"reason": payload.reason},
        )
        return updated

    @staticmethod
    async def list_builds(project_id, release_id, user):
        await get_project(project_id, user, CONTEXT_POLICY["permissions"]["build_read"])
        query = {"project_id": project_id}
        if release_id:
            query["release_id"] = release_id
        return await execution_context_repository.list_builds(query)

    @staticmethod
    async def get_build(build_id, user):
        policy = CONTEXT_POLICY
        return await get_project_entity(
            policy["collections"]["build"],
            build_id,
            user,
            policy["permissions"]["build_read"],
        )

    @staticmethod
    async def create_build(project_id, payload, user):
        policy = CONTEXT_POLICY
        await get_project(project_id, user, policy["permissions"]["build_create"])
        timestamp = now()
        build = {
            "_id": new_id(policy["id_prefixes"]["build"]),
            "project_id": project_id,
            **payload.model_dump(),
            "status": policy["statuses"]["active"],
            "revision": policy["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await execution_context_repository.insert_build(build)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["build_identifier_exists"]},
            )
        await audit(
            user.id,
            policy["events"]["build_created"],
            policy["entity_types"]["build"],
            build["_id"],
            project_id,
        )
        return build

    @staticmethod
    async def update_build(build_id, payload, user):
        policy = CONTEXT_POLICY
        build = await get_project_entity(
            policy["collections"]["build"],
            build_id,
            user,
            policy["permissions"]["build_manage"],
        )
        updated = await optimistic_patch(
            policy["collections"]["build"],
            build_id,
            build["project_id"],
            payload.expected_revision,
            payload.model_dump(),
        )
        await audit(
            user.id,
            policy["events"]["build_updated"],
            policy["entity_types"]["build"],
            build_id,
            build["project_id"],
        )
        return updated

    @staticmethod
    async def set_current_build(build_id, payload, user):
        policy = CONTEXT_POLICY
        build = await get_project_entity(
            policy["collections"]["build"],
            build_id,
            user,
            policy["permissions"]["build_manage"],
        )
        updated = await optimistic_patch(
            policy["collections"]["build"],
            build_id,
            build["project_id"],
            payload.expected_revision,
            {"is_current": True},
        )
        await execution_context_repository.set_current_build(build["project_id"], build_id)
        await audit(
            user.id,
            policy["events"]["build_set_current"],
            policy["entity_types"]["build"],
            build_id,
            build["project_id"],
        )
        return updated

    @staticmethod
    async def list_environments(project_id, user):
        policy = CONTEXT_POLICY
        await get_project(project_id, user, policy["permissions"]["environment_read"])
        items = await execution_context_repository.list_active_environments(
            project_id, policy["statuses"]["archived"]
        )
        return [clean_secret_fields(item) for item in items]

    @staticmethod
    async def get_environment(environment_id, user):
        policy = CONTEXT_POLICY
        environment = await get_project_entity(
            policy["collections"]["environment"],
            environment_id,
            user,
            policy["permissions"]["environment_read"],
        )
        return clean_secret_fields(environment)

    @staticmethod
    async def create_environment(project_id, payload, user):
        policy = CONTEXT_POLICY
        await get_project(project_id, user, policy["permissions"]["environment_create"])
        timestamp = now()
        environment = {
            "_id": new_id(policy["id_prefixes"]["environment"]),
            "project_id": project_id,
            **payload.model_dump(),
            "status": policy["statuses"]["active"],
            "revision": policy["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await execution_context_repository.insert_environment(environment)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["environment_name_exists"]},
            )
        await audit(
            user.id,
            policy["events"]["environment_created"],
            policy["entity_types"]["environment"],
            environment["_id"],
            project_id,
        )
        return clean_secret_fields(environment)

    @staticmethod
    async def update_environment(environment_id, payload, user):
        policy = CONTEXT_POLICY
        environment = await get_project_entity(
            policy["collections"]["environment"],
            environment_id,
            user,
            policy["permissions"]["environment_update"],
        )
        updated = await optimistic_patch(
            policy["collections"]["environment"],
            environment_id,
            environment["project_id"],
            payload.expected_revision,
            payload.model_dump(),
        )
        await audit(
            user.id,
            policy["events"]["environment_updated"],
            policy["entity_types"]["environment"],
            environment_id,
            environment["project_id"],
        )
        return clean_secret_fields(updated)

    @staticmethod
    async def update_environment_secrets(environment_id, payload, user):
        policy = CONTEXT_POLICY
        environment = await get_project_entity(
            policy["collections"]["environment"],
            environment_id,
            user,
            policy["permissions"]["environment_secrets"],
        )
        updated = await optimistic_patch(
            policy["collections"]["environment"],
            environment_id,
            environment["project_id"],
            payload.expected_revision,
            {"secret_refs": payload.secret_refs},
        )
        await audit(
            user.id,
            policy["events"]["environment_secrets_updated"],
            policy["entity_types"]["environment"],
            environment_id,
            environment["project_id"],
            {"names": sorted(payload.secret_refs)},
        )
        return clean_secret_fields(updated)

    @staticmethod
    async def archive_environment(environment_id, payload, user):
        policy = CONTEXT_POLICY
        environment = await get_project_entity(
            policy["collections"]["environment"],
            environment_id,
            user,
            policy["permissions"]["environment_archive"],
        )
        updated = await optimistic_patch(
            policy["collections"]["environment"],
            environment_id,
            environment["project_id"],
            payload.expected_revision,
            {
                "status": policy["statuses"]["archived"],
                "archive_reason": payload.reason,
                "archived_at": now(),
                "archived_by": user.id,
            },
        )
        await audit(
            user.id,
            policy["events"]["environment_archived"],
            policy["entity_types"]["environment"],
            environment_id,
            environment["project_id"],
            {"reason": payload.reason},
        )
        return clean_secret_fields(updated)
