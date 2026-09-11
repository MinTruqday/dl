from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now


async def validate_sources(db, project_id, payload):
    environment = await db.test_environments.find_one({"_id": payload.environment_id, "project_id": project_id, "status": {"$ne": "ARCHIVED"}})
    if not environment:
        raise HTTPException(status_code=422, detail={"code": "ENVIRONMENT_NOT_IN_PROJECT"})
    if payload.build_id and not await db.builds.find_one({"_id": payload.build_id, "project_id": project_id}):
        raise HTTPException(status_code=422, detail={"code": "BUILD_NOT_IN_PROJECT"})
    run_ids = list(dict.fromkeys(payload.affected_run_ids))
    count = await db.test_runs.count_documents({"_id": {"$in": run_ids}, "project_id": project_id, "environment_id": payload.environment_id})
    if count != len(run_ids):
        raise HTTPException(status_code=422, detail={"code": "AFFECTED_RUN_NOT_IN_ENVIRONMENT"})
    if not await db.project_members.find_one({"project_id": project_id, "user_id": payload.owner_id, "status": "ACTIVE"}):
        raise HTTPException(status_code=422, detail={"code": "INCIDENT_OWNER_NOT_PROJECT_MEMBER"})
    return environment, run_ids


async def get_incident(db, incident_id, user, permission="environmentincident.read"):
    value = await db.environment_incidents.find_one({"_id": incident_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, permission)
    return value


async def list_incidents(db, project_id, environment_id, status, user):
    await get_project(project_id, user, "environmentincident.read")
    query = {"project_id": project_id}
    if environment_id:
        query["environment_id"] = environment_id
    if status:
        query["status"] = status
    items = await db.environment_incidents.find(query).sort("observed_at", -1).to_list(1000)
    return {"items": items, "total": len(items)}


async def create_incident(db, project_id, payload, user):
    await get_project(project_id, user, "environmentincident.create")
    environment, run_ids = await validate_sources(db, project_id, payload)
    if payload.idempotency_key:
        existing = await db.environment_incidents.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        if existing:
            if existing.get("environment_id") != payload.environment_id or existing.get("type") != payload.type:
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    timestamp = now()
    previous_availability = environment.get("availability", "AVAILABLE")
    if previous_availability == "UNAVAILABLE" and environment.get("active_incident_id"):
        active_incident = await db.environment_incidents.find_one(
            {"_id": environment["active_incident_id"], "project_id": project_id}
        )
        if active_incident:
            previous_availability = active_incident.get(
                "previous_environment_availability", previous_availability
            )
    value = {
        "_id": new_id("ENVINC"),
        "project_id": project_id,
        **payload.model_dump(),
        "affected_run_ids": run_ids,
        "previous_environment_availability": previous_availability,
        "status": "OPEN",
        "resolution": "",
        "downtime": None,
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await db.environment_incidents.insert_one(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.environment_incidents.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        raise
    if payload.severity in {"BLOCKER", "CRITICAL"}:
        await db.test_environments.update_one({"_id": environment["_id"]}, {"$set": {"availability": "UNAVAILABLE", "active_incident_id": value["_id"], "updated_at": timestamp}, "$inc": {"revision": 1}})
        if run_ids:
            await db.test_runs.update_many({"_id": {"$in": run_ids}, "project_id": project_id, "status": "IN_PROGRESS"}, {"$set": {"execution_paused": True, "paused_by_environment_incident_id": value["_id"], "updated_at": timestamp}, "$inc": {"revision": 1}})
    await audit(user.id, "environment_incident_created", "EnvironmentIncident", value["_id"], project_id, {"environment_id": payload.environment_id, "severity": payload.severity, "affected_run_ids": run_ids})
    return value


async def update_incident(db, incident_id, payload, user):
    value = await get_incident(db, incident_id, user, "environmentincident.update")
    if value["status"] in {"RESOLVED", "CLOSED"}:
        raise HTTPException(status_code=409, detail={"code": "RESOLVED_INCIDENT_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "owner_id" in changes and not await db.project_members.find_one({"project_id": value["project_id"], "user_id": changes["owner_id"], "status": "ACTIVE"}):
        raise HTTPException(status_code=422, detail={"code": "INCIDENT_OWNER_NOT_PROJECT_MEMBER"})
    if "affected_run_ids" in changes:
        run_ids = list(dict.fromkeys(changes["affected_run_ids"]))
        count = await db.test_runs.count_documents({"_id": {"$in": run_ids}, "project_id": value["project_id"], "environment_id": value["environment_id"]})
        if count != len(run_ids):
            raise HTTPException(status_code=422, detail={"code": "AFFECTED_RUN_NOT_IN_ENVIRONMENT"})
        changes["affected_run_ids"] = run_ids
    changes["updated_at"] = now()
    updated = await db.environment_incidents.find_one_and_update({"_id": incident_id, "revision": payload.expected_revision, "status": {"$in": ["OPEN", "INVESTIGATING"]}}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "environment_incident_updated", "EnvironmentIncident", incident_id, value["project_id"], {"fields": sorted(changes)})
    return updated


async def transition_incident(db, incident_id, payload, user):
    permission = "environmentincident.close" if payload.status == "CLOSED" else "environmentincident.update"
    value = await get_incident(db, incident_id, user, permission)
    allowed = {("OPEN", "INVESTIGATING"), ("OPEN", "RESOLVED"), ("INVESTIGATING", "RESOLVED"), ("RESOLVED", "CLOSED")}
    if (value["status"], payload.status) not in allowed:
        raise HTTPException(status_code=409, detail={"code": "INVALID_ENVIRONMENT_INCIDENT_TRANSITION"})
    timestamp = now()
    changes = {"status": payload.status, "resolution": payload.resolution, "updated_at": timestamp}
    if payload.status == "RESOLVED":
        changes.update({"resolved_at": timestamp, "downtime": max(0, int((timestamp - value["observed_at"]).total_seconds()))})
    if payload.status == "CLOSED":
        changes.update({"closed_at": timestamp, "closed_by": user.id})
    updated = await db.environment_incidents.find_one_and_update({"_id": incident_id, "revision": payload.expected_revision, "status": value["status"]}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    if payload.status == "RESOLVED":
        remaining = await db.environment_incidents.count_documents({"project_id": value["project_id"], "environment_id": value["environment_id"], "severity": {"$in": ["BLOCKER", "CRITICAL"]}, "status": {"$in": ["OPEN", "INVESTIGATING"]}, "_id": {"$ne": incident_id}})
        if not remaining:
            await db.test_environments.update_one({"_id": value["environment_id"], "status": {"$ne": "ARCHIVED"}}, {"$set": {"availability": value.get("previous_environment_availability", "AVAILABLE"), "active_incident_id": None, "updated_at": timestamp}, "$inc": {"revision": 1}})
            await db.test_runs.update_many({"project_id": value["project_id"], "paused_by_environment_incident_id": incident_id}, {"$set": {"execution_paused": False, "paused_by_environment_incident_id": None, "updated_at": timestamp}, "$inc": {"revision": 1}})
    await audit(user.id, "environment_incident_status_changed", "EnvironmentIncident", incident_id, value["project_id"], {"from": value["status"], "to": payload.status, "downtime": changes.get("downtime")})
    return updated
