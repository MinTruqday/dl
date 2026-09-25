from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.domain.review_session import ReviewSessionCreate
from src.repositories.review import review_repository
from src.services.domain_policy import domain_policy
from src.services.review_finding import (
    add_finding,
    assign_finding,
    resolve_finding,
    verify_finding,
)
from src.services.review_session_export import export_review_csv
from src.services.review_session_query import get_review, list_reviews, validate_members


REVIEW_POLICY = domain_policy("review_session")


async def create_review(project_id, payload, user):
    policy = REVIEW_POLICY
    await get_project(project_id, user, policy["create_permission"])
    collection_name = policy["artifact_collections"].get(payload.artifact_type.upper())
    if not collection_name:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["unsupported_artifact_code"]},
        )
    artifact = await review_repository.find_artifact(
        collection_name, payload.artifact_id, project_id
    )
    if not artifact:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["artifact_not_in_project_code"]},
        )
    version_mapping = policy["artifact_version_collections"].get(
        payload.artifact_type.upper()
    )
    if version_mapping:
        version_collection, parent_field = version_mapping
        version = await review_repository.find_artifact(
            version_collection,
            payload.artifact_version_id,
            project_id,
            {parent_field: payload.artifact_id},
        )
        if not version:
            raise HTTPException(
                status_code=422,
                detail={"code": policy["artifact_version_not_in_project_code"]},
            )
    elif payload.artifact_version_id != payload.artifact_id:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["artifact_version_mismatch_code"]},
        )
    await validate_members(
        project_id,
        [payload.moderator_id, payload.author_id, *payload.reviewers, payload.scribe_id],
    )
    if payload.idempotency_key:
        existing = await review_repository.find_review_by_idempotency(
            project_id, payload.idempotency_key
        )
        if existing:
            if (
                existing.get("artifact_id") != payload.artifact_id
                or existing.get("artifact_version_id") != payload.artifact_version_id
            ):
                raise HTTPException(
                    status_code=409,
                    detail={"code": policy["idempotency_reused_code"]},
                )
            return existing
    timestamp = now()
    sequence = await review_repository.next_sequence(
        f"{project_id}:{policy['counter_suffix']}"
    )
    value = {
        "_id": new_id(policy["review_id_prefix"]),
        "project_id": project_id,
        **payload.model_dump(),
        "review_key": f"{policy['review_key_prefix']}-{int(sequence['value']):04d}",
        "checklist_version_id": payload.checklist_version,
        "reviewer_ids": payload.reviewers,
        "status": policy["planned_status"],
        "decision": None,
        "started_at": None,
        "decision_at": None,
        "completed_at": None,
        "metrics": {},
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await review_repository.insert_review(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await review_repository.find_review_by_idempotency(
                project_id, payload.idempotency_key
            )
        raise
    await audit(
        user.id,
        policy["created_event"],
        policy["entity"],
        value["_id"],
        project_id,
        {"artifact_id": payload.artifact_id, "artifact_version_id": payload.artifact_version_id},
    )
    return value


async def update_review(review_id, payload, user):
    policy = REVIEW_POLICY
    review = await get_review(review_id, user, policy["update_permission"])
    if review["status"] not in policy["editable_review_statuses"]:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["completed_immutable_code"]},
        )
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
    if review["author_id"] in participants[2:-1] or participants[0] in participants[2:-1]:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["participant_role_conflict_code"]},
        )
    await validate_members(review["project_id"], participants)
    changes["updated_at"] = now()
    value = await review_repository.update_review(
        {
            "_id": review_id,
            "revision": payload.expected_revision,
            "status": {"$in": policy["editable_review_statuses"]},
        },
        changes,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["updated_event"],
        policy["entity"],
        review_id,
        review["project_id"],
        {"fields": sorted(changes)},
    )
    return value


async def assign_reviewers(review_id, payload, user):
    policy = REVIEW_POLICY
    review = await get_review(review_id, user, policy["update_permission"])
    if review["status"] != policy["planned_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["assignment_state_invalid_code"]},
        )
    if (
        review["author_id"] in payload.reviewer_ids
        or payload.moderator_id in payload.reviewer_ids
    ):
        raise HTTPException(
            status_code=422,
            detail={"code": policy["participant_role_conflict_code"]},
        )
    await validate_members(
        review["project_id"], [payload.moderator_id, *payload.reviewer_ids, payload.scribe_id]
    )
    changes = {
        "moderator_id": payload.moderator_id,
        "reviewers": list(dict.fromkeys(payload.reviewer_ids)),
        "reviewer_ids": list(dict.fromkeys(payload.reviewer_ids)),
        "scribe_id": payload.scribe_id,
        "updated_at": now(),
    }
    value = await review_repository.update_review(
        {
            "_id": review_id,
            "revision": payload.expected_revision,
            "status": policy["planned_status"],
        },
        changes,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["reviewers_assigned_event"],
        policy["entity"],
        review_id,
        review["project_id"],
        {"reviewer_ids": changes["reviewer_ids"], "moderator_id": payload.moderator_id},
    )
    return value


async def review_metrics(review):
    policy = REVIEW_POLICY
    findings = await review_repository.list_findings(
        review["_id"], policy["finding_limit"]
    )
    timestamp = now()
    return {
        "finding_count": len(findings),
        "major_count": sum(
            1 for item in findings if item["severity"] == policy["major_severity"]
        ),
        "open_count": sum(
            1
            for item in findings
            if item["status"]
            not in {policy["resolved_finding_status"], policy["verified_finding_status"]}
        ),
        "verified_count": sum(
            1 for item in findings if item["status"] == policy["verified_finding_status"]
        ),
        "duration_seconds": max(
            0,
            int(((review.get("completed_at") or timestamp) - review["started_at"]).total_seconds()),
        )
        if review.get("started_at")
        else 0,
    }


async def record_review_decision(review_id, payload, user):
    policy = REVIEW_POLICY
    review = await get_review(review_id, user, policy["complete_permission"])
    if review.get("moderator_id") != user.id:
        raise HTTPException(status_code=403, detail={"code": policy["moderator_required_code"]})
    if review["status"] != policy["in_progress_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    metrics = await review_metrics(review)
    if (
        payload.decision in policy["accepted_decisions"]
        and metrics["major_count"]
        and metrics["open_count"]
    ):
        open_major = await review_repository.count_findings(
            {
                "review_session_id": review_id,
                "severity": policy["major_severity"],
                "status": {
                    "$nin": [
                        policy["resolved_finding_status"],
                        policy["verified_finding_status"],
                    ]
                },
            }
        )
        if open_major:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["open_major_findings_code"]},
            )
    timestamp = now()
    value = await review_repository.update_review(
        {
            "_id": review_id,
            "revision": payload.expected_revision,
            "status": policy["in_progress_status"],
        },
        {
            "status": policy["decision_pending_status"],
            "decision": payload.decision,
            "decision_note": payload.note,
            "decision_by": user.id,
            "decision_at": timestamp,
            "metrics": metrics,
            "updated_at": timestamp,
        },
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["decision_recorded_event"],
        policy["entity"],
        review_id,
        review["project_id"],
        {"decision": payload.decision, "metrics": metrics},
    )
    return value


async def transition_review(review_id, payload, user, complete=False):
    policy = REVIEW_POLICY
    review = await get_review(
        review_id,
        user,
        policy["complete_permission"] if complete else policy["update_permission"],
    )
    if review["moderator_id"] != user.id:
        raise HTTPException(status_code=403, detail={"code": policy["moderator_required_code"]})
    source, target = (
        (policy["decision_pending_status"], policy["completed_status"])
        if complete
        else (policy["planned_status"], policy["in_progress_status"])
    )
    if review["status"] != source:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    timestamp = now()
    changes = {"status": target, "updated_at": timestamp, "transition_note": payload.note}
    if complete:
        changes.update(
            {
                "completed_at": timestamp,
                "metrics": await review_metrics({**review, "completed_at": timestamp}),
            }
        )
    else:
        changes["started_at"] = timestamp
    value = await review_repository.update_review(
        {"_id": review_id, "revision": payload.expected_revision, "status": source},
        changes,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["completed_event"] if complete else policy["started_event"],
        policy["entity"],
        review_id,
        review["project_id"],
        {"decision": review.get("decision"), "metrics": changes.get("metrics")},
    )
    return value


async def transition_review_terminal(review_id, payload, user):
    policy = REVIEW_POLICY
    review = await get_review(review_id, user, policy["complete_permission"])
    if review.get("moderator_id") != user.id:
        raise HTTPException(status_code=403, detail={"code": policy["moderator_required_code"]})
    expected_source = (
        policy["planned_status"]
        if payload.target_status == policy["cancelled_status"]
        else policy["completed_status"]
    )
    if review["status"] != expected_source:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    timestamp = now()
    value = await review_repository.update_review(
        {"_id": review_id, "revision": payload.expected_revision, "status": expected_source},
        {
            "status": payload.target_status,
            "transition_note": payload.note,
            "updated_at": timestamp,
            "archived_at"
            if payload.target_status == policy["archived_status"]
            else "cancelled_at": timestamp,
        },
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["archived_event"]
        if payload.target_status == policy["archived_status"]
        else policy["cancelled_event"],
        policy["entity"],
        review_id,
        review["project_id"],
        {"note": payload.note},
    )
    return value


async def create_follow_up_review(review_id, payload, user):
    policy = REVIEW_POLICY
    review = await get_review(review_id, user, policy["create_permission"])
    if review["status"] != policy["completed_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["follow_up_requires_completed_code"]},
        )
    if review["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    create_payload = ReviewSessionCreate(
        idempotency_key=payload.idempotency_key,
        review_type=review["review_type"],
        artifact_type=review["artifact_type"],
        artifact_id=review["artifact_id"],
        artifact_version_id=review["artifact_version_id"],
        objective=payload.objective,
        checklist_version=review.get(
            "checklist_version_id",
            review.get("checklist_version", policy["default_checklist_version"]),
        ),
        moderator_id=payload.moderator_id,
        author_id=review["author_id"],
        reviewers=payload.reviewer_ids,
        scribe_id=payload.scribe_id,
        planned_at=payload.planned_at,
        checklist=review.get("checklist", []),
    )
    value = await create_review(review["project_id"], create_payload, user)
    updated = await review_repository.set_review_fields(
        value["_id"],
        {
            "parent_review_session_id": review_id,
            "follow_up_number": int(review.get("follow_up_number", 0)) + 1,
        },
    )
    await audit(
        user.id,
        policy["follow_up_created_event"],
        policy["entity"],
        updated["_id"],
        review["project_id"],
        {"parent_review_session_id": review_id},
    )
    return updated


class ReviewSessionService:
    @staticmethod
    async def list(project_id, user, status, artifact_type):
        return await list_reviews(project_id, user, status, artifact_type)

    @staticmethod
    async def create(project_id, payload, user):
        return await create_review(project_id, payload, user)

    @staticmethod
    async def get(review_id, user):
        policy = REVIEW_POLICY
        value = await get_review(review_id, user)
        value["findings"] = await review_repository.list_findings(
            review_id, policy["finding_limit"]
        )
        return value

    @staticmethod
    async def update(review_id, payload, user):
        return await update_review(review_id, payload, user)

    @staticmethod
    async def assign_reviewers(review_id, payload, user):
        return await assign_reviewers(review_id, payload, user)

    @staticmethod
    async def transition(review_id, payload, user, complete=False):
        return await transition_review(review_id, payload, user, complete)

    @staticmethod
    async def add_finding(review_id, payload, user):
        return await add_finding(review_id, payload, user)

    @staticmethod
    async def assign_finding(finding_id, payload, user):
        return await assign_finding(finding_id, payload, user)

    @staticmethod
    async def resolve_finding(finding_id, payload, user):
        return await resolve_finding(finding_id, payload, user)

    @staticmethod
    async def verify_finding(finding_id, payload, user):
        return await verify_finding(finding_id, payload, user)

    @staticmethod
    async def record_decision(review_id, payload, user):
        return await record_review_decision(review_id, payload, user)

    @staticmethod
    async def transition_terminal(review_id, payload, user):
        return await transition_review_terminal(review_id, payload, user)

    @staticmethod
    async def metrics(review_id, user):
        value = await get_review(review_id, user)
        return await review_metrics(value)

    @staticmethod
    async def create_follow_up(review_id, payload, user):
        return await create_follow_up_review(review_id, payload, user)

    @staticmethod
    async def export(review_id, user):
        value = await ReviewSessionService.get(review_id, user)
        return export_review_csv(value)
