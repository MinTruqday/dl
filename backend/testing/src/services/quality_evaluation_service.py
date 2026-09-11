from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.services.test_monitoring_service import effective_snapshot


async def get_evaluation(db, evaluation_id, user, permission="qualityevaluation.read"):
    value = await db.product_quality_evaluations.find_one({"_id": evaluation_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, permission)
    return value


async def list_evaluations(db, project_id, release_id, user):
    await get_project(project_id, user, "qualityevaluation.read")
    query = {"project_id": project_id}
    if release_id:
        query["release_id"] = release_id
    items = await db.product_quality_evaluations.find(query).sort("created_at", -1).to_list(500)
    return {"items": items, "total": len(items)}


async def create_evaluation(db, project_id, payload, user):
    await get_project(project_id, user, "qualityevaluation.create")
    if payload.idempotency_key:
        existing = await db.product_quality_evaluations.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        if existing:
            if existing.get("release_id") != payload.release_id or existing.get("build_id") != payload.build_id:
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    release = await db.releases.find_one({"_id": payload.release_id, "project_id": project_id})
    build = await db.builds.find_one({"_id": payload.build_id, "project_id": project_id})
    monitoring = await db.test_monitoring_snapshots.find_one({"_id": payload.monitoring_snapshot_id, "project_id": project_id, "release_id": payload.release_id})
    snapshots = await db.measurement_snapshots.find({"_id": {"$in": payload.measurement_snapshot_refs}, "project_id": project_id}).to_list(1000)
    if not release or not build or not monitoring or len(snapshots) != len(set(payload.measurement_snapshot_refs)):
        raise HTTPException(status_code=422, detail={"code": "QUALITY_EVALUATION_SOURCE_NOT_IN_PROJECT"})
    if any(item.get("release_id") not in {None, payload.release_id} for item in snapshots):
        raise HTTPException(status_code=422, detail={"code": "MEASUREMENT_RELEASE_MISMATCH"})
    monitoring = await effective_snapshot(monitoring)
    unresolved = await db.defects.find({"project_id": project_id, "release_id": payload.release_id, "status": {"$nin": ["CLOSED", "REJECTED"]}}, {"_id": 1, "key": 1, "severity": 1, "status": 1, "title": 1}).to_list(5000)
    timestamp = now()
    value = {"_id": new_id("PQE"), "project_id": project_id, **payload.model_dump(), "measurement_snapshots": snapshots, "exit_criteria_snapshot": monitoring.get("effective_exit_criteria_evaluation", []), "quality_gate_status": monitoring.get("effective_quality_gate_status", monitoring.get("quality_gate_status")), "unresolved_defects": unresolved, "waivers": [], "reviewed_by": [], "approved_by": None, "status": "DRAFT", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    try:
        await db.product_quality_evaluations.insert_one(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.product_quality_evaluations.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        raise
    await audit(user.id, "quality_evaluation_created", "ProductQualityEvaluation", value["_id"], project_id, {"release_id": payload.release_id, "recommendation": payload.recommendation, "measurement_snapshot_refs": payload.measurement_snapshot_refs})
    return value


async def update_evaluation(db, evaluation_id, payload, user):
    value = await get_evaluation(db, evaluation_id, user, "qualityevaluation.create")
    if value["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "QUALITY_EVALUATION_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    changes["updated_at"] = now()
    updated = await db.product_quality_evaluations.find_one_and_update({"_id": evaluation_id, "revision": payload.expected_revision, "status": "DRAFT"}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "quality_evaluation_updated", "ProductQualityEvaluation", evaluation_id, value["project_id"], {"fields": sorted(changes)})
    return updated


async def submit_evaluation(db, evaluation_id, payload, user):
    value = await get_evaluation(db, evaluation_id, user, "qualityevaluation.review")
    if value["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "INVALID_QUALITY_EVALUATION_TRANSITION"})
    updated = await db.product_quality_evaluations.find_one_and_update({"_id": evaluation_id, "revision": payload.expected_revision, "status": "DRAFT"}, {"$set": {"status": "IN_REVIEW", "submitted_by": user.id, "submitted_at": now(), "submission_note": payload.note, "updated_at": now()}, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "quality_evaluation_submitted", "ProductQualityEvaluation", evaluation_id, value["project_id"], {"note": payload.note})
    return updated


async def review_evaluation(db, evaluation_id, payload, user):
    value = await get_evaluation(db, evaluation_id, user, "qualityevaluation.review")
    if value["status"] != "IN_REVIEW":
        raise HTTPException(status_code=409, detail={"code": "QUALITY_EVALUATION_NOT_IN_REVIEW"})
    history = [*value.get("reviewed_by", []), {"actor_id": user.id, "decision": payload.decision, "note": payload.note, "at": now()}]
    changes = {"reviewed_by": history, "updated_at": now()}
    if payload.decision == "REQUEST_CHANGES":
        changes["status"] = "DRAFT"
    updated = await db.product_quality_evaluations.find_one_and_update({"_id": evaluation_id, "revision": payload.expected_revision, "status": "IN_REVIEW"}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "quality_evaluation_reviewed", "ProductQualityEvaluation", evaluation_id, value["project_id"], {"decision": payload.decision})
    return updated


async def add_waiver(db, evaluation_id, payload, user):
    value = await get_evaluation(db, evaluation_id, user, "qualityevaluation.create")
    if value["status"] not in {"DRAFT", "IN_REVIEW"}:
        raise HTTPException(status_code=409, detail={"code": "QUALITY_EVALUATION_IMMUTABLE"})
    if payload.expiry <= now():
        raise HTTPException(status_code=422, detail={"code": "WAIVER_EXPIRY_MUST_BE_FUTURE"})
    if not await db.project_members.find_one({"project_id": value["project_id"], "user_id": payload.owner_id, "status": "ACTIVE"}):
        raise HTTPException(status_code=422, detail={"code": "WAIVER_OWNER_NOT_PROJECT_MEMBER"})
    waiver = {"waiver_id": new_id("WVR"), **payload.model_dump(), "status": "PENDING", "approved_by": None, "created_by": user.id, "created_at": now()}
    updated = await db.product_quality_evaluations.find_one_and_update({"_id": evaluation_id, "revision": value["revision"], "status": {"$in": ["DRAFT", "IN_REVIEW"]}}, {"$push": {"waivers": waiver}, "$set": {"updated_at": now()}, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    await audit(user.id, "quality_waiver_created", "ProductQualityEvaluation", evaluation_id, value["project_id"], {"waiver_id": waiver["waiver_id"], "risk": waiver["risk"]})
    return updated


async def decide_waiver(db, evaluation_id, waiver_id, payload, user):
    value = await get_evaluation(db, evaluation_id, user, "qualityevaluation.waiver.approve")
    waiver = next((item for item in value.get("waivers", []) if item["waiver_id"] == waiver_id), None)
    if not waiver:
        raise HTTPException(status_code=404, detail={"code": "WAIVER_NOT_FOUND"})
    if waiver["status"] != "PENDING":
        raise HTTPException(status_code=409, detail={"code": "WAIVER_ALREADY_DECIDED"})
    waivers = [{**item, "status": "APPROVED" if payload.decision == "APPROVE" else "REJECTED", "approved_by": user.id, "approved_at": now(), "decision_note": payload.note} if item["waiver_id"] == waiver_id else item for item in value["waivers"]]
    updated = await db.product_quality_evaluations.find_one_and_update({"_id": evaluation_id, "revision": payload.expected_revision, "waivers.waiver_id": waiver_id}, {"$set": {"waivers": waivers, "updated_at": now()}, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "quality_waiver_decided", "ProductQualityEvaluation", evaluation_id, value["project_id"], {"waiver_id": waiver_id, "decision": payload.decision})
    return updated


async def approve_evaluation(db, evaluation_id, payload, user):
    value = await get_evaluation(db, evaluation_id, user, "qualityevaluation.approve")
    if value["status"] != "IN_REVIEW":
        raise HTTPException(status_code=409, detail={"code": "QUALITY_EVALUATION_NOT_IN_REVIEW"})
    if not any(item.get("decision") == "ENDORSE" for item in value.get("reviewed_by", [])):
        raise HTTPException(status_code=409, detail={"code": "QUALITY_EVALUATION_ENDORSEMENT_REQUIRED"})
    if any(item.get("status") == "PENDING" for item in value.get("waivers", [])):
        raise HTTPException(status_code=409, detail={"code": "PENDING_QUALITY_WAIVER"})
    if value.get("quality_gate_status") == "FAIL" and value["recommendation"] in {"GO", "GO_WITH_RISK"} and not any(item.get("status") == "APPROVED" for item in value.get("waivers", [])):
        raise HTTPException(status_code=409, detail={"code": "FAILED_GATE_REQUIRES_APPROVED_WAIVER"})
    timestamp = now()
    updated = await db.product_quality_evaluations.find_one_and_update({"_id": evaluation_id, "revision": payload.expected_revision, "status": "IN_REVIEW"}, {"$set": {"status": "APPROVED", "approved_by": user.id, "approved_at": timestamp, "approval_note": payload.note, "updated_at": timestamp}, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "quality_evaluation_approved", "ProductQualityEvaluation", evaluation_id, value["project_id"], {"recommendation": value["recommendation"]})
    return updated
