from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now


ARTIFACT_COLLECTIONS = {
    "REQUIREMENT": "requirements",
    "TEST_STRATEGY": "test_strategies",
    "TEST_PLAN": "test_plans",
    "TEST_CONDITION": "test_conditions",
    "TEST_CASE": "test_cases",
    "IMPACT_ANALYSIS": "impact_analyses",
    "TEST_COMPLETION": "test_completion_reports",
}

ARTIFACT_VERSION_COLLECTIONS = {
    "REQUIREMENT": ("requirement_versions", "requirement_id"),
    "TEST_CASE": ("test_case_versions", "test_case_id"),
}


async def validate_members(db, project_id, user_ids):
    values = list(dict.fromkeys(item for item in user_ids if item))
    count = await db.project_members.count_documents({"project_id": project_id, "user_id": {"$in": values}, "status": "ACTIVE"})
    if count != len(values):
        raise HTTPException(status_code=422, detail={"code": "REVIEW_PARTICIPANT_NOT_PROJECT_MEMBER"})


async def get_review(db, review_id, user, permission="reviewsession.read"):
    value = await db.review_sessions.find_one({"_id": review_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, permission)
    return value


async def list_reviews(db, project_id, user, status, artifact_type):
    await get_project(project_id, user, "reviewsession.read")
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    if artifact_type:
        query["artifact_type"] = artifact_type
    items = await db.review_sessions.find(query).sort("updated_at", -1).to_list(500)
    return {"items": items, "total": len(items)}


async def create_review(db, project_id, payload, user):
    await get_project(project_id, user, "reviewsession.create")
    collection_name = ARTIFACT_COLLECTIONS.get(payload.artifact_type.upper())
    if not collection_name:
        raise HTTPException(status_code=422, detail={"code": "UNSUPPORTED_REVIEW_ARTIFACT"})
    artifact = await getattr(db, collection_name).find_one({"_id": payload.artifact_id, "project_id": project_id})
    if not artifact:
        raise HTTPException(status_code=422, detail={"code": "REVIEW_ARTIFACT_NOT_IN_PROJECT"})
    version_mapping = ARTIFACT_VERSION_COLLECTIONS.get(payload.artifact_type.upper())
    if version_mapping:
        version_collection, parent_field = version_mapping
        version = await getattr(db, version_collection).find_one({"_id": payload.artifact_version_id, "project_id": project_id, parent_field: payload.artifact_id})
        if not version:
            raise HTTPException(status_code=422, detail={"code": "REVIEW_ARTIFACT_VERSION_NOT_IN_PROJECT"})
    elif payload.artifact_version_id != payload.artifact_id:
        raise HTTPException(status_code=422, detail={"code": "REVIEW_ARTIFACT_VERSION_MISMATCH"})
    await validate_members(db, project_id, [payload.moderator_id, payload.author_id, *payload.reviewers, payload.scribe_id])
    if payload.idempotency_key:
        existing = await db.review_sessions.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        if existing:
            if existing.get("artifact_id") != payload.artifact_id or existing.get("artifact_version_id") != payload.artifact_version_id:
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    timestamp = now()
    value = {"_id": new_id("RVS"), "project_id": project_id, **payload.model_dump(), "status": "PLANNED", "decision": None, "started_at": None, "completed_at": None, "metrics": {}, "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    try:
        await db.review_sessions.insert_one(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.review_sessions.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        raise
    await audit(user.id, "formal_review_created", "ReviewSession", value["_id"], project_id, {"artifact_id": payload.artifact_id, "artifact_version_id": payload.artifact_version_id})
    return value


async def update_review(db, review_id, payload, user):
    review = await get_review(db, review_id, user, "reviewsession.update")
    if review["status"] not in {"PLANNED", "IN_PROGRESS"}:
        raise HTTPException(status_code=409, detail={"code": "COMPLETED_REVIEW_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    participants = [changes.get("moderator_id", review["moderator_id"]), review["author_id"], *(changes.get("reviewers") or review["reviewers"]), changes.get("scribe_id", review.get("scribe_id"))]
    await validate_members(db, review["project_id"], participants)
    changes["updated_at"] = now()
    value = await db.review_sessions.find_one_and_update({"_id": review_id, "revision": payload.expected_revision, "status": {"$in": ["PLANNED", "IN_PROGRESS"]}}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "formal_review_updated", "ReviewSession", review_id, review["project_id"], {"fields": sorted(changes)})
    return value


async def add_finding(db, review_id, payload, user):
    review = await get_review(db, review_id, user, "reviewsession.finding.manage")
    if review["status"] == "COMPLETED":
        raise HTTPException(status_code=409, detail={"code": "COMPLETED_REVIEW_IMMUTABLE"})
    await validate_members(db, review["project_id"], [payload.owner_id])
    timestamp = now()
    value = {"_id": new_id("RVF"), "review_session_id": review_id, "project_id": review["project_id"], **payload.model_dump(), "status": "OPEN", "resolution": "", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await db.review_findings.insert_one(value)
    await audit(user.id, "formal_review_finding_created", "ReviewFinding", value["_id"], review["project_id"], {"review_session_id": review_id, "severity": value["severity"]})
    return value


async def update_finding(db, finding_id, payload, user):
    finding = await db.review_findings.find_one({"_id": finding_id})
    if not finding:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(finding["project_id"], user, "reviewsession.finding.manage")
    review = await db.review_sessions.find_one({"_id": finding["review_session_id"]})
    if not review or review["status"] == "COMPLETED":
        raise HTTPException(status_code=409, detail={"code": "COMPLETED_REVIEW_IMMUTABLE"})
    changes = {"status": payload.status, "resolution": payload.resolution, "updated_at": now()}
    value = await db.review_findings.find_one_and_update({"_id": finding_id, "revision": payload.expected_revision}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "formal_review_finding_updated", "ReviewFinding", finding_id, finding["project_id"], changes)
    return value


async def transition_review(db, review_id, payload, user, complete=False):
    review = await get_review(db, review_id, user, "reviewsession.complete" if complete else "reviewsession.update")
    if review["moderator_id"] != user.id:
        raise HTTPException(status_code=403, detail={"code": "REVIEW_MODERATOR_REQUIRED"})
    source, target = ("IN_PROGRESS", "COMPLETED") if complete else ("PLANNED", "IN_PROGRESS")
    if review["status"] != source:
        raise HTTPException(status_code=409, detail={"code": "INVALID_REVIEW_TRANSITION"})
    if complete and not payload.decision:
        raise HTTPException(status_code=422, detail={"code": "REVIEW_DECISION_REQUIRED"})
    findings = await db.review_findings.find({"review_session_id": review_id}).to_list(1000)
    open_major = sum(1 for item in findings if item["severity"] == "MAJOR" and item["status"] not in {"RESOLVED", "ACCEPTED"})
    if complete and payload.decision in {"ACCEPTED", "ACCEPTED_WITH_ACTIONS"} and open_major:
        raise HTTPException(status_code=409, detail={"code": "OPEN_MAJOR_REVIEW_FINDINGS"})
    timestamp = now()
    changes = {"status": target, "updated_at": timestamp, "transition_note": payload.note}
    if complete:
        changes.update({"decision": payload.decision, "completed_at": timestamp, "metrics": {"finding_count": len(findings), "major_count": sum(1 for item in findings if item["severity"] == "MAJOR"), "open_count": sum(1 for item in findings if item["status"] not in {"RESOLVED", "ACCEPTED"}), "duration_seconds": max(0, int((timestamp - review["started_at"]).total_seconds())) if review.get("started_at") else 0}})
    else:
        changes["started_at"] = timestamp
    value = await db.review_sessions.find_one_and_update({"_id": review_id, "revision": payload.expected_revision, "status": source}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "formal_review_completed" if complete else "formal_review_started", "ReviewSession", review_id, review["project_id"], {"decision": payload.decision, "metrics": changes.get("metrics")})
    return value
