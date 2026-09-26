from fastapi import HTTPException

from src.core.common import audit, get_project, new_id, now
from src.repositories.review import review_repository
from src.services.domain_policy import domain_policy
from src.services.review_session_query import get_review, validate_members


REVIEW_POLICY = domain_policy("review_session")


async def add_finding(review_id, payload, user):
    policy = REVIEW_POLICY
    review = await get_review(review_id, user, policy["finding_manage_permission"])
    if review["status"] != policy["in_progress_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["completed_immutable_code"]})
    await validate_members(review["project_id"], [payload.owner_id])
    timestamp = now()
    value = {
        "_id": new_id(policy["finding_id_prefix"]),
        "review_session_id": review_id,
        "project_id": review["project_id"],
        **payload.model_dump(),
        "status": policy["open_finding_status"],
        "resolution": "",
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await review_repository.insert_finding(value)
    await audit(
        user.id,
        policy["finding_created_event"],
        policy["finding_entity"],
        value["_id"],
        review["project_id"],
        {"review_session_id": review_id, "severity": value["severity"]},
    )
    return value


async def update_finding(finding_id, payload, user):
    policy = REVIEW_POLICY
    finding = await review_repository.find_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(finding["project_id"], user, policy["finding_manage_permission"])
    review = await review_repository.find_review(finding["review_session_id"])
    if not review or review["status"] not in policy["finding_review_statuses"]:
        raise HTTPException(status_code=409, detail={"code": policy["completed_immutable_code"]})
    changes = {"status": payload.status, "resolution": payload.resolution, "updated_at": now()}
    value = await review_repository.update_finding(
        {"_id": finding_id, "revision": payload.expected_revision},
        changes,
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["finding_updated_event"],
        policy["finding_entity"],
        finding_id,
        finding["project_id"],
        changes,
    )
    return value


async def get_finding_for_update(finding_id, user):
    policy = REVIEW_POLICY
    finding = await review_repository.find_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(finding["project_id"], user, policy["finding_manage_permission"])
    review = await review_repository.find_review(finding["review_session_id"])
    if not review or review["status"] != policy["in_progress_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["finding_state_invalid_code"]})
    return finding, review


async def assign_finding(finding_id, payload, user):
    policy = REVIEW_POLICY
    finding, review = await get_finding_for_update(finding_id, user)
    await validate_members(review["project_id"], [payload.owner_id])
    timestamp = now()
    value = await review_repository.update_finding(
        {
            "_id": finding_id,
            "revision": payload.expected_revision,
            "status": {"$in": policy["assignable_finding_statuses"]},
        },
        {
            "owner_id": payload.owner_id,
            "status": policy["in_progress_status"],
            "assigned_by": user.id,
            "assigned_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["finding_assigned_event"],
        policy["finding_entity"],
        finding_id,
        finding["project_id"],
        {"owner_id": payload.owner_id},
    )
    return value


async def resolve_finding(finding_id, payload, user):
    policy = REVIEW_POLICY
    finding, _ = await get_finding_for_update(finding_id, user)
    if finding.get("owner_id") != user.id:
        membership = await review_repository.find_active_member(
            finding["project_id"], user.id, policy["active_member_status"]
        )
        if (membership or {}).get("project_role") != policy["qa_role"]:
            raise HTTPException(
                status_code=403,
                detail={"code": policy["finding_owner_required_code"]},
            )
    timestamp = now()
    value = await review_repository.update_finding(
        {
            "_id": finding_id,
            "revision": payload.expected_revision,
            "status": {"$in": policy["assignable_finding_statuses"]},
        },
        {
            "status": policy["resolved_finding_status"],
            "resolution": payload.resolution,
            "resolved_by": user.id,
            "resolved_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["finding_resolved_event"],
        policy["finding_entity"],
        finding_id,
        finding["project_id"],
        {"resolution": payload.resolution},
    )
    return value


async def verify_finding(finding_id, payload, user):
    policy = REVIEW_POLICY
    finding, review = await get_finding_for_update(finding_id, user)
    reviewers = review.get("reviewer_ids", review.get("reviewers", []))
    if user.id not in reviewers and review.get("moderator_id") != user.id:
        raise HTTPException(status_code=403, detail={"code": policy["verifier_required_code"]})
    if finding.get("resolved_by") == user.id:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["independent_verification_required_code"]},
        )
    timestamp = now()
    value = await review_repository.update_finding(
        {
            "_id": finding_id,
            "revision": payload.expected_revision,
            "status": policy["resolved_finding_status"],
        },
        {
            "status": policy["verified_finding_status"],
            "verification_note": payload.note,
            "verified_by": user.id,
            "verified_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not value:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["finding_verified_event"],
        policy["finding_entity"],
        finding_id,
        finding["project_id"],
        {"note": payload.note},
    )
    return value
