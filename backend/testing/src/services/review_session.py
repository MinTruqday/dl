from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.domain.review_session import ReviewSessionCreate

ARTIFACT_COLLECTIONS = {
    "REQUIREMENT": "requirements",
    "TEST_STRATEGY": "test_strategies",
    "TEST_PLAN": "test_plans",
    "TEST_CONDITION": "test_conditions",
    "TEST_CASE": "test_cases",
    "IMPACT_ANALYSIS": "impact_analyses",
    "TEST_COMPLETION": "test_completion_reports",
    "COMPLETION_REPORT": "test_completion_reports",
    "STATUS_REPORT": "test_status_reports",
}

ARTIFACT_VERSION_COLLECTIONS = {
    "REQUIREMENT": ("requirement_versions", "requirement_id"),
    "TEST_CASE": ("test_case_versions", "test_case_id"),
}


async def validate_members(db, project_id, user_ids):
    values = list(dict.fromkeys(item for item in user_ids if item))
    count = await db.project_members.count_documents(
        {"project_id": project_id, "user_id": {"$in": values}, "status": "ACTIVE"}
    )
    if count != len(values):
        raise HTTPException(
            status_code=422, detail={"code": "REVIEW_PARTICIPANT_NOT_PROJECT_MEMBER"}
        )


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
    artifact = await getattr(db, collection_name).find_one(
        {"_id": payload.artifact_id, "project_id": project_id}
    )
    if not artifact:
        raise HTTPException(status_code=422, detail={"code": "REVIEW_ARTIFACT_NOT_IN_PROJECT"})
    version_mapping = ARTIFACT_VERSION_COLLECTIONS.get(payload.artifact_type.upper())
    if version_mapping:
        version_collection, parent_field = version_mapping
        version = await getattr(db, version_collection).find_one(
            {
                "_id": payload.artifact_version_id,
                "project_id": project_id,
                parent_field: payload.artifact_id,
            }
        )
        if not version:
            raise HTTPException(
                status_code=422, detail={"code": "REVIEW_ARTIFACT_VERSION_NOT_IN_PROJECT"}
            )
    elif payload.artifact_version_id != payload.artifact_id:
        raise HTTPException(status_code=422, detail={"code": "REVIEW_ARTIFACT_VERSION_MISMATCH"})
    await validate_members(
        db,
        project_id,
        [payload.moderator_id, payload.author_id, *payload.reviewers, payload.scribe_id],
    )
    if payload.idempotency_key:
        existing = await db.review_sessions.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            if (
                existing.get("artifact_id") != payload.artifact_id
                or existing.get("artifact_version_id") != payload.artifact_version_id
            ):
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    timestamp = now()
    sequence = await db.counters.find_one_and_update(
        {"_id": f"{project_id}:formal-review"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    value = {
        "_id": new_id("RVS"),
        "project_id": project_id,
        **payload.model_dump(),
        "review_key": f"RVS-{int(sequence['value']):04d}",
        "checklist_version_id": payload.checklist_version,
        "reviewer_ids": payload.reviewers,
        "status": "PLANNED",
        "decision": None,
        "started_at": None,
        "decision_at": None,
        "completed_at": None,
        "metrics": {},
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await db.review_sessions.insert_one(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.review_sessions.find_one(
                {"project_id": project_id, "idempotency_key": payload.idempotency_key}
            )
        raise
    await audit(
        user.id,
        "formal_review_created",
        "ReviewSession",
        value["_id"],
        project_id,
        {"artifact_id": payload.artifact_id, "artifact_version_id": payload.artifact_version_id},
    )
    return value


async def update_review(db, review_id, payload, user):
    review = await get_review(db, review_id, user, "reviewsession.update")
    if review["status"] not in {"PLANNED", "IN_PROGRESS"}:
        raise HTTPException(status_code=409, detail={"code": "COMPLETED_REVIEW_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "reviewers" in changes:
        changes["reviewers"] = list(dict.fromkeys(changes["reviewers"]))
        changes["reviewer_ids"] = changes["reviewers"]
    participants = [
        changes.get("moderator_id", review["moderator_id"]),
        review["author_id"],
        *(changes.get("reviewers") or review["reviewers"]),
        changes.get("scribe_id", review.get("scribe_id")),
    ]
    if (
        participants[0] == review["author_id"]
        or review["author_id"] in participants[2:-1]
        or participants[0] in participants[2:-1]
    ):
        raise HTTPException(status_code=422, detail={"code": "REVIEW_PARTICIPANT_ROLE_CONFLICT"})
    await validate_members(db, review["project_id"], participants)
    changes["updated_at"] = now()
    value = await db.review_sessions.find_one_and_update(
        {
            "_id": review_id,
            "revision": payload.expected_revision,
            "status": {"$in": ["PLANNED", "IN_PROGRESS"]},
        },
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "formal_review_updated",
        "ReviewSession",
        review_id,
        review["project_id"],
        {"fields": sorted(changes)},
    )
    return value


async def assign_reviewers(db, review_id, payload, user):
    review = await get_review(db, review_id, user, "reviewsession.update")
    if review["status"] != "PLANNED":
        raise HTTPException(status_code=409, detail={"code": "REVIEW_ASSIGNMENT_STATE_INVALID"})
    if (
        review["author_id"] == payload.moderator_id
        or review["author_id"] in payload.reviewer_ids
        or payload.moderator_id in payload.reviewer_ids
    ):
        raise HTTPException(status_code=422, detail={"code": "REVIEW_PARTICIPANT_ROLE_CONFLICT"})
    await validate_members(
        db, review["project_id"], [payload.moderator_id, *payload.reviewer_ids, payload.scribe_id]
    )
    changes = {
        "moderator_id": payload.moderator_id,
        "reviewers": list(dict.fromkeys(payload.reviewer_ids)),
        "reviewer_ids": list(dict.fromkeys(payload.reviewer_ids)),
        "scribe_id": payload.scribe_id,
        "updated_at": now(),
    }
    value = await db.review_sessions.find_one_and_update(
        {"_id": review_id, "revision": payload.expected_revision, "status": "PLANNED"},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "formal_review_reviewers_assigned",
        "ReviewSession",
        review_id,
        review["project_id"],
        {"reviewer_ids": changes["reviewer_ids"], "moderator_id": payload.moderator_id},
    )
    return value


async def add_finding(db, review_id, payload, user):
    review = await get_review(db, review_id, user, "reviewsession.finding.manage")
    if review["status"] != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail={"code": "COMPLETED_REVIEW_IMMUTABLE"})
    await validate_members(db, review["project_id"], [payload.owner_id])
    timestamp = now()
    value = {
        "_id": new_id("RVF"),
        "review_session_id": review_id,
        "project_id": review["project_id"],
        **payload.model_dump(),
        "status": "OPEN",
        "resolution": "",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await db.review_findings.insert_one(value)
    await audit(
        user.id,
        "review_finding_created",
        "ReviewFinding",
        value["_id"],
        review["project_id"],
        {"review_session_id": review_id, "severity": value["severity"]},
    )
    return value


async def update_finding(db, finding_id, payload, user):
    finding = await db.review_findings.find_one({"_id": finding_id})
    if not finding:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(finding["project_id"], user, "reviewsession.finding.manage")
    review = await db.review_sessions.find_one({"_id": finding["review_session_id"]})
    if not review or review["status"] not in {"IN_PROGRESS", "DECISION_PENDING"}:
        raise HTTPException(status_code=409, detail={"code": "COMPLETED_REVIEW_IMMUTABLE"})
    changes = {"status": payload.status, "resolution": payload.resolution, "updated_at": now()}
    value = await db.review_findings.find_one_and_update(
        {"_id": finding_id, "revision": payload.expected_revision},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "formal_review_finding_updated",
        "ReviewFinding",
        finding_id,
        finding["project_id"],
        changes,
    )
    return value


async def get_finding_for_update(db, finding_id, user):
    finding = await db.review_findings.find_one({"_id": finding_id})
    if not finding:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(finding["project_id"], user, "reviewsession.finding.manage")
    review = await db.review_sessions.find_one({"_id": finding["review_session_id"]})
    if not review or review["status"] != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail={"code": "REVIEW_FINDING_STATE_INVALID"})
    return finding, review


async def assign_finding(db, finding_id, payload, user):
    finding, review = await get_finding_for_update(db, finding_id, user)
    await validate_members(db, review["project_id"], [payload.owner_id])
    value = await db.review_findings.find_one_and_update(
        {
            "_id": finding_id,
            "revision": payload.expected_revision,
            "status": {"$in": ["OPEN", "IN_PROGRESS"]},
        },
        {
            "$set": {
                "owner_id": payload.owner_id,
                "status": "IN_PROGRESS",
                "assigned_by": user.id,
                "assigned_at": now(),
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "formal_review_finding_assigned",
        "ReviewFinding",
        finding_id,
        finding["project_id"],
        {"owner_id": payload.owner_id},
    )
    return value


async def resolve_finding(db, finding_id, payload, user):
    finding, _ = await get_finding_for_update(db, finding_id, user)
    if finding.get("owner_id") != user.id:
        membership = await db.project_members.find_one(
            {"project_id": finding["project_id"], "user_id": user.id, "status": "ACTIVE"}
        )
        if (membership or {}).get("project_role") != "QA_LEAD":
            raise HTTPException(status_code=403, detail={"code": "REVIEW_FINDING_OWNER_REQUIRED"})
    value = await db.review_findings.find_one_and_update(
        {
            "_id": finding_id,
            "revision": payload.expected_revision,
            "status": {"$in": ["OPEN", "IN_PROGRESS"]},
        },
        {
            "$set": {
                "status": "RESOLVED",
                "resolution": payload.resolution,
                "resolved_by": user.id,
                "resolved_at": now(),
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "formal_review_finding_resolved",
        "ReviewFinding",
        finding_id,
        finding["project_id"],
        {"resolution": payload.resolution},
    )
    return value


async def verify_finding(db, finding_id, payload, user):
    finding, review = await get_finding_for_update(db, finding_id, user)
    reviewers = review.get("reviewer_ids", review.get("reviewers", []))
    if user.id not in reviewers and review.get("moderator_id") != user.id:
        raise HTTPException(status_code=403, detail={"code": "REVIEW_VERIFIER_REQUIRED"})
    if finding.get("resolved_by") == user.id:
        raise HTTPException(
            status_code=409, detail={"code": "REVIEW_INDEPENDENT_VERIFICATION_REQUIRED"}
        )
    value = await db.review_findings.find_one_and_update(
        {"_id": finding_id, "revision": payload.expected_revision, "status": "RESOLVED"},
        {
            "$set": {
                "status": "VERIFIED",
                "verification_note": payload.note,
                "verified_by": user.id,
                "verified_at": now(),
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "review_finding_verified",
        "ReviewFinding",
        finding_id,
        finding["project_id"],
        {"note": payload.note},
    )
    return value


async def review_metrics(db, review):
    findings = await db.review_findings.find({"review_session_id": review["_id"]}).to_list(1000)
    timestamp = now()
    return {
        "finding_count": len(findings),
        "major_count": sum(1 for item in findings if item["severity"] == "MAJOR"),
        "open_count": sum(1 for item in findings if item["status"] not in {"RESOLVED", "VERIFIED"}),
        "verified_count": sum(1 for item in findings if item["status"] == "VERIFIED"),
        "duration_seconds": max(
            0,
            int(((review.get("completed_at") or timestamp) - review["started_at"]).total_seconds()),
        )
        if review.get("started_at")
        else 0,
    }


async def record_review_decision(db, review_id, payload, user):
    review = await get_review(db, review_id, user, "reviewsession.complete")
    if review.get("moderator_id") != user.id:
        raise HTTPException(status_code=403, detail={"code": "REVIEW_MODERATOR_REQUIRED"})
    if review["status"] != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail={"code": "INVALID_REVIEW_TRANSITION"})
    metrics = await review_metrics(db, review)
    if (
        payload.decision in {"ACCEPTED", "ACCEPTED_WITH_ACTIONS"}
        and metrics["major_count"]
        and metrics["open_count"]
    ):
        open_major = await db.review_findings.count_documents(
            {
                "review_session_id": review_id,
                "severity": "MAJOR",
                "status": {"$nin": ["RESOLVED", "VERIFIED"]},
            }
        )
        if open_major:
            raise HTTPException(status_code=409, detail={"code": "OPEN_MAJOR_REVIEW_FINDINGS"})
    timestamp = now()
    value = await db.review_sessions.find_one_and_update(
        {"_id": review_id, "revision": payload.expected_revision, "status": "IN_PROGRESS"},
        {
            "$set": {
                "status": "DECISION_PENDING",
                "decision": payload.decision,
                "decision_note": payload.note,
                "decision_by": user.id,
                "decision_at": timestamp,
                "metrics": metrics,
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "formal_review_decision_recorded",
        "ReviewSession",
        review_id,
        review["project_id"],
        {"decision": payload.decision, "metrics": metrics},
    )
    return value


async def transition_review(db, review_id, payload, user, complete=False):
    review = await get_review(
        db, review_id, user, "reviewsession.complete" if complete else "reviewsession.update"
    )
    if review["moderator_id"] != user.id:
        raise HTTPException(status_code=403, detail={"code": "REVIEW_MODERATOR_REQUIRED"})
    source, target = ("DECISION_PENDING", "COMPLETED") if complete else ("PLANNED", "IN_PROGRESS")
    if review["status"] != source:
        raise HTTPException(status_code=409, detail={"code": "INVALID_REVIEW_TRANSITION"})
    timestamp = now()
    changes = {"status": target, "updated_at": timestamp, "transition_note": payload.note}
    if complete:
        changes.update(
            {
                "completed_at": timestamp,
                "metrics": await review_metrics(db, {**review, "completed_at": timestamp}),
            }
        )
    else:
        changes["started_at"] = timestamp
    value = await db.review_sessions.find_one_and_update(
        {"_id": review_id, "revision": payload.expected_revision, "status": source},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "formal_review_completed" if complete else "formal_review_started",
        "ReviewSession",
        review_id,
        review["project_id"],
        {"decision": review.get("decision"), "metrics": changes.get("metrics")},
    )
    return value


async def transition_review_terminal(db, review_id, payload, user):
    review = await get_review(db, review_id, user, "reviewsession.complete")
    if review.get("moderator_id") != user.id:
        raise HTTPException(status_code=403, detail={"code": "REVIEW_MODERATOR_REQUIRED"})
    expected_source = "PLANNED" if payload.target_status == "CANCELLED" else "COMPLETED"
    if review["status"] != expected_source:
        raise HTTPException(status_code=409, detail={"code": "INVALID_REVIEW_TRANSITION"})
    timestamp = now()
    value = await db.review_sessions.find_one_and_update(
        {"_id": review_id, "revision": payload.expected_revision, "status": expected_source},
        {
            "$set": {
                "status": payload.target_status,
                "transition_note": payload.note,
                "updated_at": timestamp,
                "archived_at" if payload.target_status == "ARCHIVED" else "cancelled_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "formal_review_archived"
        if payload.target_status == "ARCHIVED"
        else "formal_review_cancelled",
        "ReviewSession",
        review_id,
        review["project_id"],
        {"note": payload.note},
    )
    return value


async def create_follow_up_review(db, review_id, payload, user):
    review = await get_review(db, review_id, user, "reviewsession.create")
    if review["status"] != "COMPLETED":
        raise HTTPException(status_code=409, detail={"code": "FOLLOW_UP_REQUIRES_COMPLETED_REVIEW"})
    if review["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    create_payload = ReviewSessionCreate(
        idempotency_key=payload.idempotency_key,
        review_type=review["review_type"],
        artifact_type=review["artifact_type"],
        artifact_id=review["artifact_id"],
        artifact_version_id=review["artifact_version_id"],
        objective=payload.objective,
        checklist_version=review.get("checklist_version_id", review.get("checklist_version", "1")),
        moderator_id=payload.moderator_id,
        author_id=review["author_id"],
        reviewers=payload.reviewer_ids,
        scribe_id=payload.scribe_id,
        planned_at=payload.planned_at,
        checklist=review.get("checklist", []),
    )
    value = await create_review(db, review["project_id"], create_payload, user)
    updated = await db.review_sessions.find_one_and_update(
        {"_id": value["_id"]},
        {
            "$set": {
                "parent_review_session_id": review_id,
                "follow_up_number": int(review.get("follow_up_number", 0)) + 1,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    await audit(
        user.id,
        "formal_review_follow_up_created",
        "ReviewSession",
        updated["_id"],
        review["project_id"],
        {"parent_review_session_id": review_id},
    )
    return updated
