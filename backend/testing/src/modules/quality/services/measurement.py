import hashlib
import json

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.domain.measurement import validate_threshold_order
from src.repositories.measurement import measurement_repository
from src.services.domain_policy import domain_policy
from src.services.measurement_engine import (
    compute_custom_metric,
    compute_metric,
    validate_formula_source,
)
from src.services.measurement_export import export_metric_csv

async def list_definitions(project_id, user):
    policy = domain_policy("measurement")
    await get_project(project_id, user, policy["read_permission"])
    items = await measurement_repository.list_definitions(
        project_id, policy["definition_limit"]
    )
    return {"items": items, "total": len(items)}


async def create_definition(project_id, payload, user):
    policy = domain_policy("measurement")
    await get_project(project_id, user, policy["manage_permission"])
    if payload.idempotency_key:
        existing = await measurement_repository.find_definition_idempotency(
            project_id, payload.idempotency_key
        )
        if existing:
            if existing.get("key") != payload.key:
                raise HTTPException(
                    status_code=409, detail={"code": policy["idempotency_reused_code"]}
                )
            return existing
    validation = validate_formula_source(
        payload.formula_type, payload.formula, payload.data_sources
    )
    if not validation["valid"]:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["definition_invalid_code"], "errors": validation["errors"]},
        )
    latest = await measurement_repository.find_latest_definition(project_id, payload.key)
    timestamp = now()
    value = {
        "_id": new_id(policy["definition_id_prefix"]),
        "project_id": project_id,
        **payload.model_dump(),
        "version": int(latest.get("version", 0)) + 1 if latest else policy["initial_version"],
        "status": policy["draft_status"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await measurement_repository.insert_definition(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await measurement_repository.find_definition_idempotency(
                project_id, payload.idempotency_key
            )
        raise
    await audit(
        user.id,
        policy["definition_created_event"],
        policy["definition_entity_type"],
        value["_id"],
        project_id,
        {"key": value["key"], "version": value["version"]},
    )
    return value


async def update_definition(definition_id, payload, user):
    policy = domain_policy("measurement")
    value = await measurement_repository.find_definition(definition_id)
    if not value:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(value["project_id"], user, policy["manage_permission"])
    if value["status"] != policy["draft_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["active_immutable_code"]}
        )
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    try:
        validate_threshold_order(
            value["key"],
            changes.get("target", value.get("target")),
            changes.get("warning_threshold", value.get("warning_threshold")),
            changes.get("critical_threshold", value.get("critical_threshold")),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["invalid_threshold_code"], "message": str(error)},
        ) from error
    validation = validate_formula_source(
        changes.get("formula_type", value.get("formula_type", policy["built_in_formula_type"])),
        changes.get("formula", value["formula"]),
        changes.get("data_sources", value["data_sources"]),
    )
    if not validation["valid"]:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["definition_invalid_code"], "errors": validation["errors"]},
        )
    changes["updated_at"] = now()
    updated = await measurement_repository.update_definition(
        definition_id, payload.expected_revision, policy["draft_status"], changes
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["definition_updated_event"],
        policy["definition_entity_type"],
        definition_id,
        value["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def transition_definition(definition_id, payload, user):
    policy = domain_policy("measurement")
    value = await measurement_repository.find_definition(definition_id)
    if not value:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(value["project_id"], user, policy["manage_permission"])
    allowed = {tuple(item) for item in policy["allowed_transitions"]}
    if (value["status"], payload.status) not in allowed:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    timestamp = now()
    if payload.status == policy["active_status"]:
        await measurement_repository.archive_other_active_definitions(
            value["project_id"],
            value["key"],
            definition_id,
            policy["active_status"],
            policy["archived_status"],
            timestamp,
        )
    try:
        updated = await measurement_repository.update_definition(
            definition_id,
            payload.expected_revision,
            value["status"],
            {
                "status": payload.status,
                "transition_note": payload.note,
                "updated_at": timestamp,
            },
        )
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=409, detail={"code": policy["active_definition_exists_code"]}
        ) from error
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    event = (
        policy["definition_activated_event"]
        if payload.status == policy["active_status"]
        else policy["definition_status_changed_event"]
    )
    await audit(
        user.id,
        event,
        policy["definition_entity_type"],
        definition_id,
        value["project_id"],
        {"from": value["status"], "to": payload.status},
    )
    return updated


async def create_snapshot(project_id, payload, user):
    policy = domain_policy("measurement")
    await get_project(project_id, user, policy["snapshot_permission"])
    definition = await measurement_repository.find_definition(
        payload.definition_id,
        {"project_id": project_id, "status": policy["active_status"]},
    )
    if not definition:
        raise HTTPException(
            status_code=422, detail={"code": policy["active_definition_required_code"]}
        )
    if payload.release_id and not await measurement_repository.find_release(
        payload.release_id, project_id
    ):
        raise HTTPException(status_code=422, detail={"code": policy["release_not_in_project_code"]})
    if payload.idempotency_key:
        existing = await measurement_repository.find_snapshot_idempotency(
            project_id, payload.idempotency_key
        )
        if existing:
            if (
                existing.get("measurement_definition_id") != payload.definition_id
                or existing.get("release_id") != payload.release_id
            ):
                raise HTTPException(status_code=409, detail={"code": policy["idempotency_reused_code"]})
            return existing
    if definition.get("formula_type") == policy["custom_formula_type"]:
        value, source = await compute_custom_metric(project_id, payload.release_id, definition)
    else:
        value, source = await compute_metric(project_id, payload.release_id, definition["key"])
    if value is None:
        raise HTTPException(
            status_code=422,
            detail={
                "code": policy["source_unavailable_code"],
                "metric": definition["key"],
                "source": source,
            },
        )
    fingerprint = hashlib.sha256(
        json.dumps(source, sort_keys=True, default=str).encode()
    ).hexdigest()
    timestamp = now()
    snapshot = {
        "_id": new_id(policy["snapshot_id_prefix"]),
        "project_id": project_id,
        "release_id": payload.release_id,
        "measurement_definition_id": definition["_id"],
        "measurement_definition_version": definition["version"],
        "measurement_key": definition["key"],
        "value": value,
        "unit": definition["unit"],
        "dimensions": payload.dimensions,
        "source": source,
        "source_fingerprint": fingerprint,
        "measured_at": timestamp,
        "idempotency_key": payload.idempotency_key,
        "created_by": user.id,
        "created_at": timestamp,
    }
    try:
        await measurement_repository.insert_snapshot(snapshot)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await measurement_repository.find_snapshot_idempotency(
                project_id, payload.idempotency_key
            )
        raise
    await audit(
        user.id,
        policy["snapshot_created_event"],
        policy["snapshot_entity_type"],
        snapshot["_id"],
        project_id,
        {"key": definition["key"], "value": value, "source_fingerprint": fingerprint},
    )
    return snapshot


async def list_snapshots(project_id, user, definition_id, release_id):
    policy = domain_policy("measurement")
    await get_project(project_id, user, policy["read_permission"])
    query = {"project_id": project_id}
    if definition_id:
        query["measurement_definition_id"] = definition_id
    if release_id:
        query["release_id"] = release_id
    items = await measurement_repository.list_snapshots(
        query, -1, policy["snapshot_limit"]
    )
    return {"items": items, "total": len(items)}


async def version_definition(definition_id, payload, user):
    policy = domain_policy("measurement")
    source = await measurement_repository.find_definition(definition_id)
    if not source:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(source["project_id"], user, policy["manage_permission"])
    if source["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    existing = await measurement_repository.find_definition_idempotency(
        source["project_id"], payload.idempotency_key
    )
    if existing:
        if existing.get("supersedes_definition_id") != definition_id:
            raise HTTPException(status_code=409, detail={"code": policy["idempotency_reused_code"]})
        return existing
    latest = await measurement_repository.find_latest_definition(
        source["project_id"], source["key"]
    )
    excluded = {
        "_id",
        "status",
        "revision",
        "created_by",
        "created_at",
        "updated_at",
        "transition_note",
        "idempotency_key",
    }
    timestamp = now()
    value = {key: item for key, item in source.items() if key not in excluded}
    value.update(
        {
            "_id": new_id(policy["definition_id_prefix"]),
            "version": int((latest or {}).get("version", 0)) + 1,
            "status": policy["draft_status"],
            "revision": policy["initial_revision"],
            "idempotency_key": payload.idempotency_key,
            "supersedes_definition_id": definition_id,
            "version_note": payload.note,
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    try:
        await measurement_repository.insert_definition(value)
    except DuplicateKeyError:
        duplicate = await measurement_repository.find_definition_idempotency(
            source["project_id"], payload.idempotency_key
        )
        if duplicate:
            return duplicate
        raise
    await audit(
        user.id,
        policy["definition_versioned_event"],
        policy["definition_entity_type"],
        value["_id"],
        source["project_id"],
        {"supersedes_definition_id": definition_id, "version": value["version"]},
    )
    return value


async def validate_definition(definition_id, user):
    policy = domain_policy("measurement")
    value = await measurement_repository.find_definition(definition_id)
    if not value:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(value["project_id"], user, policy["read_permission"])
    result = validate_formula_source(
        value.get("formula_type", policy["built_in_formula_type"]),
        value["formula"],
        value["data_sources"],
    )
    return {
        **result,
        "definition_id": definition_id,
        "key": value["key"],
        "version": value["version"],
    }


async def measurement_trend(definition_id, release_id, user):
    policy = domain_policy("measurement")
    definition = await measurement_repository.find_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(definition["project_id"], user, policy["read_permission"])
    query = {"project_id": definition["project_id"], "measurement_key": definition["key"]}
    if release_id:
        query["release_id"] = release_id
    items = await measurement_repository.list_snapshots(
        query, 1, policy["trend_limit"]
    )
    return {
        "definition_id": definition_id,
        "measurement_key": definition["key"],
        "items": items,
        "total": len(items),
    }


async def compare_measurement_releases(project_id, release_a, release_b, user):
    policy = domain_policy("measurement")
    await get_project(project_id, user, policy["read_permission"])
    releases = await measurement_repository.count_releases(
        project_id, [release_a, release_b]
    )
    if releases != len({release_a, release_b}):
        raise HTTPException(status_code=422, detail={"code": policy["release_not_in_project_code"]})
    rows = await measurement_repository.list_snapshots(
        {"project_id": project_id, "release_id": {"$in": [release_a, release_b]}},
        -1,
        policy["comparison_limit"],
    )
    latest = {}
    for item in rows:
        latest.setdefault((item["release_id"], item["measurement_key"]), item)
    keys = sorted({key for _, key in latest})
    items = [
        {
            "measurement_key": key,
            "release_a": latest.get((release_a, key)),
            "release_b": latest.get((release_b, key)),
            "delta": round(
                float(latest[(release_b, key)]["value"]) - float(latest[(release_a, key)]["value"]),
                4,
            )
            if (release_a, key) in latest and (release_b, key) in latest
            else None,
        }
        for key in keys
    ]
    return {"release_a": release_a, "release_b": release_b, "items": items}


def threshold_level(definition, value):
    policy = domain_policy("measurement")
    key = definition["key"]
    critical = definition.get("critical_threshold")
    warning = definition.get("warning_threshold")
    if value is None:
        return policy["no_data_level"]
    if key in policy["higher_is_worse_keys"]:
        if critical is not None and value >= critical:
            return policy["critical_level"]
        if warning is not None and value >= warning:
            return policy["warning_level"]
    else:
        if critical is not None and value <= critical:
            return policy["critical_level"]
        if warning is not None and value <= warning:
            return policy["warning_level"]
    return policy["normal_level"]


async def measurement_alerts(project_id, user):
    policy = domain_policy("measurement")
    await get_project(project_id, user, policy["read_permission"])
    definitions = await measurement_repository.list_active_definitions(
        project_id, policy["active_status"], policy["definition_limit"]
    )
    items = []
    for definition in definitions:
        snapshot = await measurement_repository.find_latest_snapshot(
            project_id, definition["_id"]
        )
        level = threshold_level(definition, snapshot.get("value") if snapshot else None)
        if level in policy["alert_levels"]:
            items.append(
                {
                    "definition_id": definition["_id"],
                    "measurement_key": definition["key"],
                    "level": level,
                    "value": snapshot.get("value") if snapshot else None,
                    "snapshot_id": snapshot.get("_id") if snapshot else None,
                }
            )
    return {"items": items, "total": len(items)}


async def pin_metric(definition_id, payload, user):
    policy = domain_policy("measurement")
    definition = await measurement_repository.find_definition(definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(definition["project_id"], user, policy["read_permission"])
    key = {
        "project_id": definition["project_id"],
        "user_id": user.id,
        "measurement_key": definition["key"],
    }
    if payload.pinned:
        await measurement_repository.set_dashboard_pin(key, definition_id, now())
    else:
        await measurement_repository.delete_dashboard_pin(key)
    await audit(
        user.id,
        policy["dashboard_pin_changed_event"],
        policy["definition_entity_type"],
        definition_id,
        definition["project_id"],
        {"pinned": payload.pinned},
    )
    return {**key, "definition_id": definition_id, "pinned": payload.pinned}


class MeasurementService:
    @staticmethod
    async def list_definitions(project_id, user):
        return await list_definitions(project_id, user)

    @staticmethod
    async def create_definition(project_id, payload, user):
        return await create_definition(project_id, payload, user)

    @staticmethod
    async def update_definition(definition_id, payload, user):
        return await update_definition(definition_id, payload, user)

    @staticmethod
    async def version_definition(definition_id, payload, user):
        return await version_definition(definition_id, payload, user)

    @staticmethod
    async def transition_definition(definition_id, payload, user):
        return await transition_definition(definition_id, payload, user)

    @staticmethod
    async def list_snapshots(project_id, user, definition_id, release_id):
        return await list_snapshots(project_id, user, definition_id, release_id)

    @staticmethod
    async def create_snapshot(project_id, payload, user):
        return await create_snapshot(project_id, payload, user)

    @staticmethod
    async def get_snapshot(snapshot_id, user):
        policy = domain_policy("measurement")
        value = await measurement_repository.find_snapshot(snapshot_id)
        if not value:
            raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
        await get_project(value["project_id"], user, policy["read_permission"])
        return value

    @staticmethod
    async def trend(definition_id, release_id, user):
        return await measurement_trend(definition_id, release_id, user)

    @staticmethod
    async def compare_releases(project_id, release_a, release_b, user):
        return await compare_measurement_releases(project_id, release_a, release_b, user)

    @staticmethod
    async def alerts(project_id, user):
        return await measurement_alerts(project_id, user)

    @staticmethod
    async def validate(definition_id, user):
        return await validate_definition(definition_id, user)

    @staticmethod
    async def pin(definition_id, payload, user):
        return await pin_metric(definition_id, payload, user)

    @staticmethod
    async def export(definition_id, user):
        policy = domain_policy("measurement")
        definition = await measurement_repository.find_definition(definition_id)
        if not definition:
            raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
        await get_project(definition["project_id"], user, policy["export_permission"])
        snapshots = await measurement_repository.list_snapshots(
            {
                "project_id": definition["project_id"],
                "measurement_key": definition["key"],
            },
            1,
            policy["export_limit"],
        )
        return definition, export_metric_csv(definition, snapshots)
