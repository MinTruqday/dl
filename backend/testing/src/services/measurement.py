import hashlib
import json
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.domain.measurement import validate_threshold_order


MONITORING_KEYS = {"REQUIREMENT_COVERAGE": "requirement_coverage", "ACCEPTANCE_CRITERION_COVERAGE": "acceptance_criteria_coverage", "TEST_CONDITION_COVERAGE": "test_condition_coverage", "EXECUTION_PROGRESS": "execution_percent", "PASS_RATE": "pass_rate"}


def ratio(numerator, denominator):
    if not denominator:
        return None
    return round(float(numerator) * 100 / float(denominator), 4)


async def compute_metric(db, project_id, release_id, key):
    source = {"key": key, "release_id": release_id}
    if key in MONITORING_KEYS:
        query = {"project_id": project_id}
        if release_id:
            query["release_id"] = release_id
        snapshot = await db.test_monitoring_snapshots.find_one(query, sort=[("snapshot_at", -1)])
        if not snapshot:
            return None, source
        metrics = snapshot.get("metrics", {})
        value = metrics.get(MONITORING_KEYS[key])
        source.update({"monitoring_snapshot_id": snapshot["_id"], "monitoring_source_fingerprint": snapshot.get("source_fingerprint")})
        return value, source
    if key == "BLOCKED_RATE":
        query = {"project_id": project_id}
        if release_id:
            query["release_id"] = release_id
        snapshot = await db.test_monitoring_snapshots.find_one(query, sort=[("snapshot_at", -1)])
        if not snapshot:
            return None, source
        metrics = snapshot.get("metrics", {})
        denominator = int(metrics.get("pass", 0)) + int(metrics.get("fail", 0)) + int(metrics.get("blocked", 0))
        source.update({"monitoring_snapshot_id": snapshot["_id"], "blocked": metrics.get("blocked", 0), "decisive": denominator})
        return ratio(metrics.get("blocked", 0), denominator), source
    if key == "STALE_TEST_RATIO":
        total = await db.test_cases.count_documents({"project_id": project_id, "status": {"$ne": "ARCHIVED"}})
        stale = await db.test_cases.count_documents({"project_id": project_id, "status": "NEEDS_UPDATE"})
        source.update({"test_case_count": total, "stale_count": stale})
        return ratio(stale, total), source
    if key == "AUTOMATION_COVERAGE":
        total = await db.test_case_versions.count_documents({"project_id": project_id, "status": {"$in": ["APPROVED", "FROZEN"]}})
        automated = await db.automation_script_drafts.count_documents({"project_id": project_id, "status": "APPROVED"})
        source.update({"test_case_version_count": total, "approved_script_count": automated})
        return ratio(min(automated, total), total), source
    defects = {"project_id": project_id}
    runs = {"project_id": project_id}
    if release_id:
        defects["release_id"] = release_id
        runs["release_id"] = release_id
    if key == "DEFECT_REOPEN_RATE":
        total = await db.defects.count_documents(defects)
        reopened = await db.defects.count_documents({**defects, "$or": [{"reopen_count": {"$gt": 0}}, {"history.action": "REOPENED"}]})
        source.update({"defect_count": total, "reopened_count": reopened})
        return ratio(reopened, total), source
    if key == "CRITICAL_DEFECT_AGING":
        rows = await db.defects.find({**defects, "severity": {"$in": ["BLOCKER", "CRITICAL"]}, "status": {"$nin": ["CLOSED", "REJECTED"]}}, {"created_at": 1}).to_list(10000)
        if not rows:
            return None, source
        timestamp = now()
        value = sum(max(0, (timestamp - item["created_at"]).total_seconds()) for item in rows) / len(rows) / 86400
        source["defect_ids"] = [item["_id"] for item in rows]
        return round(value, 4), source
    if key == "MEAN_TIME_TO_RETEST":
        rows = await db.defects.find({**defects, "resolved_at": {"$type": "date"}, "retested_at": {"$type": "date"}}, {"resolved_at": 1, "retested_at": 1}).to_list(10000)
        durations = [(item["retested_at"] - item["resolved_at"]).total_seconds() / 3600 for item in rows if item["retested_at"] >= item["resolved_at"]]
        source["sample_size"] = len(durations)
        return round(sum(durations) / len(durations), 4) if durations else None, source
    if key == "REQUIREMENT_VOLATILITY":
        total = await db.requirements.count_documents({"project_id": project_id})
        changed = len(await db.requirement_versions.distinct("requirement_id", {"project_id": project_id, "version": {"$gt": 1}}))
        source.update({"requirement_count": total, "changed_requirement_count": changed})
        return ratio(changed, total), source
    if key == "IMPACT_PROPOSAL_ACCEPTANCE_RATE":
        query = {"project_id": project_id}
        total = await db.maintenance_proposals.count_documents(query)
        accepted = await db.maintenance_proposals.count_documents({**query, "status": {"$in": ["ACCEPTED", "APPROVED", "APPLIED"]}})
        source.update({"proposal_count": total, "accepted_count": accepted})
        return ratio(accepted, total), source
    if key == "REGRESSION_EFFECTIVENESS":
        rows = await db.regression_recommendations.find({"project_id": project_id}, {"selected_test_case_ids": 1, "detected_defect_ids": 1}).to_list(10000)
        selected = sum(len(item.get("selected_test_case_ids", [])) for item in rows)
        detected = sum(len(item.get("detected_defect_ids", [])) for item in rows)
        source.update({"selected_count": selected, "detected_defect_count": detected})
        return ratio(detected, selected), source
    if key == "AUTOMATION_PASS_STABILITY":
        rows = await db.automation_executions.find(runs, {"status": 1}).to_list(10000)
        completed = [item for item in rows if item.get("status") in {"PASSED", "FAILED", "COMPLETED"}]
        passed = sum(1 for item in completed if item.get("status") == "PASSED")
        source.update({"execution_count": len(completed), "passed_count": passed})
        return ratio(passed, len(completed)), source
    if key in {"ESCAPED_DEFECT_RATE", "DEFECT_REMOVAL_EFFICIENCY"}:
        production = await db.environment_incidents.count_documents({"project_id": project_id, "production": True, "linked_defect_ids.0": {"$exists": True}})
        removed = await db.defects.count_documents({**defects, "status": "CLOSED"})
        if not production:
            return None, {**source, "reason": "PRODUCTION_INCIDENT_DATA_UNAVAILABLE"}
        denominator = production + removed
        source.update({"escaped_count": production, "removed_count": removed})
        return (ratio(production, denominator) if key == "ESCAPED_DEFECT_RATE" else ratio(removed, denominator)), source
    return None, {**source, "reason": "METRIC_SOURCE_UNAVAILABLE"}


async def list_definitions(db, project_id, user):
    await get_project(project_id, user, "measurement.read")
    items = await db.measurement_definitions.find({"project_id": project_id}).sort([("key", 1), ("version", -1)]).to_list(1000)
    return {"items": items, "total": len(items)}


async def create_definition(db, project_id, payload, user):
    await get_project(project_id, user, "measurement.manage")
    if payload.idempotency_key:
        existing = await db.measurement_definitions.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        if existing:
            if existing.get("key") != payload.key:
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    latest = await db.measurement_definitions.find_one({"project_id": project_id, "key": payload.key}, sort=[("version", -1)])
    timestamp = now()
    value = {"_id": new_id("METDEF"), "project_id": project_id, **payload.model_dump(), "version": int(latest.get("version", 0)) + 1 if latest else 1, "status": "DRAFT", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    try:
        await db.measurement_definitions.insert_one(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.measurement_definitions.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        raise
    await audit(user.id, "measurement_definition_created", "MeasurementDefinition", value["_id"], project_id, {"key": value["key"], "version": value["version"]})
    return value


async def update_definition(db, definition_id, payload, user):
    value = await db.measurement_definitions.find_one({"_id": definition_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, "measurement.manage")
    if value["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "ACTIVE_MEASUREMENT_DEFINITION_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    try:
        validate_threshold_order(value["key"], changes.get("target", value.get("target")), changes.get("warning_threshold", value.get("warning_threshold")), changes.get("critical_threshold", value.get("critical_threshold")))
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"code": "INVALID_MEASUREMENT_THRESHOLDS", "message": str(error)}) from error
    changes["updated_at"] = now()
    updated = await db.measurement_definitions.find_one_and_update({"_id": definition_id, "revision": payload.expected_revision, "status": "DRAFT"}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "measurement_definition_updated", "MeasurementDefinition", definition_id, value["project_id"], {"fields": sorted(changes)})
    return updated


async def transition_definition(db, definition_id, payload, user):
    value = await db.measurement_definitions.find_one({"_id": definition_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, "measurement.manage")
    allowed = {("DRAFT", "ACTIVE"), ("ACTIVE", "RETIRED")}
    if (value["status"], payload.status) not in allowed:
        raise HTTPException(status_code=409, detail={"code": "INVALID_MEASUREMENT_TRANSITION"})
    timestamp = now()
    if payload.status == "ACTIVE":
        await db.measurement_definitions.update_many({"project_id": value["project_id"], "key": value["key"], "status": "ACTIVE", "_id": {"$ne": definition_id}}, {"$set": {"status": "RETIRED", "updated_at": timestamp}, "$inc": {"revision": 1}})
    try:
        updated = await db.measurement_definitions.find_one_and_update({"_id": definition_id, "revision": payload.expected_revision, "status": value["status"]}, {"$set": {"status": payload.status, "transition_note": payload.note, "updated_at": timestamp}, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail={"code": "ACTIVE_MEASUREMENT_DEFINITION_EXISTS"}) from error
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "measurement_definition_status_changed", "MeasurementDefinition", definition_id, value["project_id"], {"from": value["status"], "to": payload.status})
    return updated


async def create_snapshot(db, project_id, payload, user):
    await get_project(project_id, user, "measurement.snapshot.create")
    definition = await db.measurement_definitions.find_one({"_id": payload.definition_id, "project_id": project_id, "status": "ACTIVE"})
    if not definition:
        raise HTTPException(status_code=422, detail={"code": "ACTIVE_MEASUREMENT_DEFINITION_REQUIRED"})
    if payload.release_id and not await db.releases.find_one({"_id": payload.release_id, "project_id": project_id}):
        raise HTTPException(status_code=422, detail={"code": "RELEASE_NOT_IN_PROJECT"})
    if payload.idempotency_key:
        existing = await db.measurement_snapshots.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        if existing:
            if existing.get("measurement_definition_id") != payload.definition_id or existing.get("release_id") != payload.release_id:
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    value, source = await compute_metric(db, project_id, payload.release_id, definition["key"])
    if value is None:
        raise HTTPException(status_code=422, detail={"code": "METRIC_SOURCE_UNAVAILABLE", "metric": definition["key"], "source": source})
    fingerprint = hashlib.sha256(json.dumps(source, sort_keys=True, default=str).encode()).hexdigest()
    timestamp = now()
    snapshot = {"_id": new_id("METSNP"), "project_id": project_id, "release_id": payload.release_id, "measurement_definition_id": definition["_id"], "measurement_definition_version": definition["version"], "measurement_key": definition["key"], "value": value, "unit": definition["unit"], "dimensions": payload.dimensions, "source": source, "source_fingerprint": fingerprint, "measured_at": timestamp, "idempotency_key": payload.idempotency_key, "created_by": user.id, "created_at": timestamp}
    try:
        await db.measurement_snapshots.insert_one(snapshot)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.measurement_snapshots.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        raise
    await audit(user.id, "measurement_snapshot_created", "MeasurementSnapshot", snapshot["_id"], project_id, {"key": definition["key"], "value": value, "source_fingerprint": fingerprint})
    return snapshot


async def list_snapshots(db, project_id, user, definition_id, release_id):
    await get_project(project_id, user, "measurement.read")
    query = {"project_id": project_id}
    if definition_id:
        query["measurement_definition_id"] = definition_id
    if release_id:
        query["release_id"] = release_id
    items = await db.measurement_snapshots.find(query).sort("measured_at", -1).to_list(2000)
    return {"items": items, "total": len(items)}
