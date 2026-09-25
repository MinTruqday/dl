from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.repositories.environment_incident import environment_incident_repository
from src.services.domain_policy import domain_policy


INCIDENT_POLICY = domain_policy("environment_incident")


async def validate_sources(project_id, payload):
    environment = await environment_incident_repository.find_environment(
        payload.environment_id,
        project_id,
        INCIDENT_POLICY["archived_environment_status"],
    )
    if not environment:
        raise HTTPException(status_code=422, detail={"code": INCIDENT_POLICY["environment_not_in_project_code"]})
    if payload.build_id and not await environment_incident_repository.find_build(
        payload.build_id, project_id
    ):
        raise HTTPException(status_code=422, detail={"code": INCIDENT_POLICY["build_not_in_project_code"]})
    run_ids = list(dict.fromkeys(payload.affected_run_ids))
    count = await environment_incident_repository.count_environment_runs(
        run_ids, project_id, payload.environment_id
    )
    if count != len(run_ids):
        raise HTTPException(status_code=422, detail={"code": INCIDENT_POLICY["affected_run_invalid_code"]})
    if not await environment_incident_repository.find_active_member(
        project_id, payload.owner_id, INCIDENT_POLICY["active_member_status"]
    ):
        raise HTTPException(status_code=422, detail={"code": INCIDENT_POLICY["owner_not_member_code"]})
    return environment, run_ids


async def get_incident(incident_id, user, permission=None):
    value = await environment_incident_repository.find_incident(incident_id)
    if not value:
        raise HTTPException(status_code=404, detail={"code": INCIDENT_POLICY["entity_not_found_code"]})
    await get_project(value["project_id"], user, permission or INCIDENT_POLICY["read_permission"])
    return value


async def list_incidents(project_id, environment_id, status, user):
    await get_project(project_id, user, INCIDENT_POLICY["read_permission"])
    query = {"project_id": project_id}
    if environment_id:
        query["environment_id"] = environment_id
    if status:
        query["status"] = status
    items = await environment_incident_repository.list_incidents(
        query, INCIDENT_POLICY["list_limit"]
    )
    return {"items": items, "total": len(items)}


async def create_incident(project_id, payload, user):
    await get_project(project_id, user, INCIDENT_POLICY["create_permission"])
    policy = INCIDENT_POLICY
    environment, run_ids = await validate_sources(project_id, payload)
    if payload.idempotency_key:
        existing = await environment_incident_repository.find_by_idempotency_key(
            project_id, payload.idempotency_key
        )
        if existing:
            if (
                existing.get("environment_id") != payload.environment_id
                or existing.get("type") != payload.type
            ):
                raise HTTPException(status_code=409, detail={"code": policy["idempotency_reused_code"]})
            return existing
    timestamp = now()
    sequence = await environment_incident_repository.next_sequence(
        f"{project_id}:{policy['counter_suffix']}"
    )
    previous_availability = environment.get("availability", policy["available_status"])
    if previous_availability == policy["unavailable_status"] and environment.get("active_incident_id"):
        active_incident = await environment_incident_repository.find_incident(
            environment["active_incident_id"], project_id
        )
        if active_incident:
            previous_availability = active_incident.get(
                "previous_environment_availability", previous_availability
            )
    value = {
        "_id": new_id(policy["key_prefix"]),
        "incident_key": f"{policy['key_prefix']}-{int(sequence['value']):0{policy['key_width']}d}",
        "project_id": project_id,
        **payload.model_dump(),
        "affected_run_ids": run_ids,
        "previous_environment_availability": previous_availability,
        "status": policy["initial_status"],
        "resolution": "",
        "downtime_start": payload.observed_at,
        "downtime_end": None,
        "downtime": None,
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await environment_incident_repository.insert_incident(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await environment_incident_repository.find_by_idempotency_key(
                project_id, payload.idempotency_key
            )
        raise
    if payload.severity in policy["blocking_severities"]:
        await environment_incident_repository.mark_environment_unavailable(
            environment["_id"], value["_id"], policy["unavailable_status"], timestamp
        )
        if run_ids:
            await environment_incident_repository.pause_runs(
                run_ids,
                project_id,
                value["_id"],
                policy["in_progress_run_status"],
                timestamp,
            )
    await audit(
        user.id,
        policy["created_event"],
        policy["entity"],
        value["_id"],
        project_id,
        {
            "environment_id": payload.environment_id,
            "severity": payload.severity,
            "affected_run_ids": run_ids,
        },
    )
    return value


async def update_incident(incident_id, payload, user):
    policy = INCIDENT_POLICY
    value = await get_incident(incident_id, user, policy["update_permission"])
    if value["status"] in policy["immutable_statuses"]:
        raise HTTPException(status_code=409, detail={"code": policy["immutable_code"]})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "owner_id" in changes and not await environment_incident_repository.find_active_member(
        value["project_id"], changes["owner_id"], policy["active_member_status"]
    ):
        raise HTTPException(status_code=422, detail={"code": policy["owner_not_member_code"]})
    if "affected_run_ids" in changes:
        run_ids = list(dict.fromkeys(changes["affected_run_ids"]))
        count = await environment_incident_repository.count_environment_runs(
            run_ids, value["project_id"], value["environment_id"]
        )
        if count != len(run_ids):
            raise HTTPException(status_code=422, detail={"code": policy["affected_run_invalid_code"]})
        changes["affected_run_ids"] = run_ids
    changes["updated_at"] = now()
    updated = await environment_incident_repository.update_incident(
        incident_id, payload.expected_revision, policy["active_statuses"], changes
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["updated_event"],
        policy["entity"],
        incident_id,
        value["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def transition_incident(incident_id, payload, user):
    policy = INCIDENT_POLICY
    permission = (
        policy["close_permission"]
        if payload.status == policy["closed_status"]
        else policy["update_permission"]
    )
    value = await get_incident(incident_id, user, permission)
    if payload.status not in policy["transitions"].get(value["status"], []):
        raise HTTPException(
            status_code=409, detail={"code": policy["invalid_transition_code"]}
        )
    timestamp = now()
    changes = {"status": payload.status, "resolution": payload.resolution, "updated_at": timestamp}
    if payload.status == policy["resolved_status"]:
        changes.update(
            {
                "resolved_at": timestamp,
                "downtime_end": timestamp,
                "downtime": max(0, int((timestamp - value["observed_at"]).total_seconds())),
            }
        )
    if payload.status == policy["closed_status"]:
        changes.update({"closed_at": timestamp, "closed_by": user.id})
    updated = await environment_incident_repository.update_incident(
        incident_id, payload.expected_revision, value["status"], changes
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    if payload.status == policy["resolved_status"]:
        remaining = await environment_incident_repository.count_other_active_blocking(
            value["project_id"],
            value["environment_id"],
            incident_id,
            policy["blocking_severities"],
            policy["active_statuses"],
        )
        if not remaining:
            await environment_incident_repository.restore_environment(
                value["environment_id"],
                value.get("previous_environment_availability", policy["available_status"]),
                policy["archived_environment_status"],
                timestamp,
            )
            await environment_incident_repository.resume_runs(
                value["project_id"], incident_id, timestamp
            )
    event = (
        policy["closed_event"]
        if payload.status == policy["closed_status"]
        else policy["status_changed_event"]
    )
    await audit(
        user.id,
        event,
        policy["entity"],
        incident_id,
        value["project_id"],
        {"from": value["status"], "to": payload.status, "downtime": changes.get("downtime")},
    )
    return updated


class EnvironmentIncidentService:
    @staticmethod
    async def list(project_id, environment_id, status, user):
        return await list_incidents(project_id, environment_id, status, user)

    @staticmethod
    async def create(project_id, payload, user):
        return await create_incident(project_id, payload, user)

    @staticmethod
    async def get(incident_id, user):
        return await get_incident(incident_id, user)

    @staticmethod
    async def update(incident_id, payload, user):
        return await update_incident(incident_id, payload, user)

    @staticmethod
    async def investigate(incident_id, payload, user):
        if payload.status == INCIDENT_POLICY["closed_status"]:
            raise HTTPException(
                status_code=422,
                detail={"code": INCIDENT_POLICY["close_endpoint_required_code"]},
            )
        return await transition_incident(incident_id, payload, user)

    @staticmethod
    async def close(incident_id, payload, user):
        if payload.status != INCIDENT_POLICY["closed_status"]:
            raise HTTPException(
                status_code=422,
                detail={"code": INCIDENT_POLICY["close_status_required_code"]},
            )
        return await transition_incident(incident_id, payload, user)

    @staticmethod
    async def transition(incident_id, payload, user):
        return await transition_incident(incident_id, payload, user)
