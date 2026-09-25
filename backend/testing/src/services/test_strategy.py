import re

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now, page_payload
from src.domain.test_strategy import (
    TestStrategyFields,
    compare_strategy_snapshots,
    strategy_completeness,
    strategy_hash,
    strategy_snapshot,
)
from src.repositories.test_strategy import test_strategy_repository
from src.services.domain_policy import domain_policy


STRATEGY_POLICY = domain_policy("test_strategy")


async def get_strategy_for_user(strategy_id, user, permission=None):
    policy = STRATEGY_POLICY
    strategy = await test_strategy_repository.get(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=404, detail={"code": policy["error_codes"]["not_found"]}
        )
    await get_project(
        strategy["project_id"], user, permission or policy["permissions"]["read"]
    )
    return strategy


async def list_strategies(project_id, user, query_text, status, version, page, page_size):
    await get_project(project_id, user, STRATEGY_POLICY["permissions"]["read"])
    query = {"project_id": project_id}
    if query_text:
        query["$or"] = [
            {"key": {"$regex": re.escape(query_text), "$options": "i"}},
            {"name": {"$regex": re.escape(query_text), "$options": "i"}},
        ]
    if status:
        query["status"] = status
    if version is not None:
        query["version"] = version
    items, total = await test_strategy_repository.list(query, (page - 1) * page_size, page_size)
    return page_payload(items, page, page_size, total)


async def create_strategy(project_id, payload, user):
    policy = STRATEGY_POLICY
    await get_project(project_id, user, policy["permissions"]["create"])
    timestamp = now()
    strategy_id = new_id(policy["id_prefix"])
    value = {
        "_id": strategy_id,
        "lineage_id": strategy_id,
        "project_id": project_id,
        **payload.model_dump(),
        "version": policy["initial_version"],
        "status": policy["statuses"]["draft"],
        "active_approved": False,
        "reviewed_by": [],
        "approval_history": [],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await test_strategy_repository.create(value)
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["key_version_exists"]}
        ) from error
    await audit(
        user.id,
        policy["events"]["created"],
        policy["entity_type"],
        strategy_id,
        project_id,
        {"key": value["key"], "version": policy["initial_version"]},
    )
    return value


async def update_strategy(strategy_id, payload, user):
    policy = STRATEGY_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    strategy = await get_strategy_for_user(
        strategy_id, user, policy["permissions"]["update"]
    )
    if strategy["status"] == statuses["archived"]:
        raise HTTPException(
            status_code=409,
            detail={"code": codes["artifact_archived"], "artifact_type": policy["artifact_type"]},
        )
    if strategy["status"] not in set(policy["editable_statuses"]):
        raise HTTPException(
            status_code=409,
            detail={"code": codes["not_draft"], "status": strategy["status"]},
        )
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    merged = {**strategy, **changes}
    TestStrategyFields.model_validate(merged)
    changes["updated_at"] = now()
    updated = await test_strategy_repository.update(
        strategy_id,
        strategy["project_id"],
        payload.expected_revision,
        set(policy["editable_statuses"]),
        changes,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["updated"],
        policy["entity_type"],
        strategy_id,
        strategy["project_id"],
        {"fields": sorted(field for field in changes if field != "updated_at")},
    )
    return updated


async def submit_strategy(strategy_id, payload, user):
    policy = STRATEGY_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    strategy = await get_strategy_for_user(
        strategy_id, user, policy["permissions"]["submit_review"]
    )
    completeness = strategy_completeness(strategy)
    if not completeness["ready_for_review"]:
        raise HTTPException(
            status_code=409, detail={"code": codes["incomplete"], **completeness}
        )
    if not strategy.get("reviewer_ids"):
        raise HTTPException(status_code=422, detail={"code": codes["reviewers_required"]})
    if not any(reviewer_id != user.id for reviewer_id in strategy.get("reviewer_ids", [])):
        raise HTTPException(
            status_code=422, detail={"code": codes["independent_reviewer_required"]}
        )
    updated = await test_strategy_repository.update(
        strategy_id,
        strategy["project_id"],
        payload.expected_revision,
        {statuses["draft"]},
        {
            "status": statuses["in_review"],
            "submitted_by": user.id,
            "submitted_at": now(),
            "review_note": payload.note,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["transition_conflict"]})
    await audit(
        user.id,
        policy["events"]["submitted"],
        policy["entity_type"],
        strategy_id,
        strategy["project_id"],
        {"note": payload.note},
    )
    return updated


async def request_strategy_changes(strategy_id, payload, user):
    policy = STRATEGY_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    strategy = await get_strategy_for_user(
        strategy_id, user, policy["permissions"]["review"]
    )
    if user.id not in strategy.get("reviewer_ids", []):
        raise HTTPException(
            status_code=403, detail={"code": codes["review_assignment_required"]}
        )
    if user.id == strategy.get("created_by"):
        raise HTTPException(
            status_code=403, detail={"code": codes["self_review_not_allowed"]}
        )
    updated = await test_strategy_repository.update(
        strategy_id,
        strategy["project_id"],
        payload.expected_revision,
        {statuses["in_review"]},
        {
            "status": statuses["draft"],
            "reviewed_by": list(dict.fromkeys([*strategy.get("reviewed_by", []), user.id])),
            "change_request": payload.note,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["transition_conflict"]})
    await audit(
        user.id,
        policy["events"]["changes_requested"],
        policy["entity_type"],
        strategy_id,
        strategy["project_id"],
        {"note": payload.note},
    )
    return updated


async def approve_strategy(strategy_id, payload, user):
    policy = STRATEGY_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    strategy = await get_strategy_for_user(
        strategy_id, user, policy["permissions"]["approve"]
    )
    if strategy["status"] != statuses["in_review"]:
        raise HTTPException(status_code=409, detail={"code": codes["not_in_review"]})
    if payload.expected_revision != strategy["revision"]:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    completeness = strategy_completeness(strategy)
    if not completeness["ready_for_review"]:
        raise HTTPException(
            status_code=409, detail={"code": codes["incomplete"], **completeness}
        )
    if not strategy.get("reviewed_by"):
        raise HTTPException(status_code=409, detail={"code": codes["review_required"]})
    timestamp = now()
    existing = await test_strategy_repository.active_approved(
        strategy["project_id"], statuses["approved"], strategy_id
    )
    if existing:
        await test_strategy_repository.update(
            existing["_id"],
            strategy["project_id"],
            existing["revision"],
            {statuses["approved"]},
            {
                "status": statuses["superseded"],
                "active_approved": False,
                "superseded_by": strategy_id,
                "superseded_at": timestamp,
                "updated_at": timestamp,
            },
        )
    snapshot = strategy_snapshot(strategy)
    approval = {
        "actor_id": user.id,
        "action": policy["approval_action"],
        "note": payload.note,
        "at": timestamp,
    }
    try:
        updated = await test_strategy_repository.update(
            strategy_id,
            strategy["project_id"],
            payload.expected_revision,
            {statuses["in_review"]},
            {
                "status": statuses["approved"],
                "active_approved": True,
                "approved_by": user.id,
                "approved_at": timestamp,
                "approved_snapshot": snapshot,
                "snapshot_hash": strategy_hash(strategy),
                "approval_history": [*strategy.get("approval_history", []), approval],
                "updated_at": timestamp,
            },
        )
    except DuplicateKeyError as error:
        if existing:
            await test_strategy_repository.update(
                existing["_id"],
                strategy["project_id"],
                existing["revision"] + 1,
                {statuses["superseded"]},
                {"status": statuses["approved"], "active_approved": True, "updated_at": now()},
            )
        raise HTTPException(
            status_code=409, detail={"code": codes["active_conflict"]}
        ) from error
    if not updated:
        if existing:
            await test_strategy_repository.update(
                existing["_id"],
                strategy["project_id"],
                existing["revision"] + 1,
                {statuses["superseded"]},
                {"status": statuses["approved"], "active_approved": True, "updated_at": now()},
            )
        raise HTTPException(status_code=409, detail={"code": codes["transition_conflict"]})
    await audit(
        user.id,
        policy["events"]["approved"],
        policy["entity_type"],
        strategy_id,
        strategy["project_id"],
        {
            "snapshot_hash": updated["snapshot_hash"],
            "superseded_strategy_id": existing.get("_id") if existing else None,
        },
    )
    return updated


async def create_strategy_version(strategy_id, payload, user):
    policy = STRATEGY_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    strategy = await get_strategy_for_user(
        strategy_id, user, policy["permissions"]["create_version"]
    )
    if strategy["status"] not in set(policy["version_source_statuses"]):
        raise HTTPException(
            status_code=409, detail={"code": codes["version_source_not_approved"]}
        )
    if payload.expected_revision != strategy["revision"]:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    version = await test_strategy_repository.next_version(strategy["lineage_id"])
    timestamp = now()
    fields = {field: strategy.get(field) for field in TestStrategyFields.model_fields}
    value = {
        "_id": new_id(policy["id_prefix"]),
        "lineage_id": strategy["lineage_id"],
        "project_id": strategy["project_id"],
        "key": strategy["key"],
        **fields,
        "version": version,
        "status": statuses["draft"],
        "active_approved": False,
        "reviewed_by": [],
        "approval_history": [],
        "version_reason": payload.change_reason,
        "derived_from_strategy_id": strategy_id,
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await test_strategy_repository.create(value)
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=409, detail={"code": codes["version_conflict"]}
        ) from error
    await audit(
        user.id,
        policy["events"]["version_created"],
        policy["entity_type"],
        value["_id"],
        strategy["project_id"],
        {"source_strategy_id": strategy_id, "version": version, "reason": payload.change_reason},
    )
    return value


async def validate_strategy(strategy_id, user):
    strategy = await get_strategy_for_user(
        strategy_id, user, STRATEGY_POLICY["permissions"]["review"]
    )
    return strategy_completeness(strategy)


async def review_strategy(strategy_id, payload, user):
    policy = STRATEGY_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    strategy = await get_strategy_for_user(
        strategy_id, user, policy["permissions"]["review"]
    )
    if strategy["status"] != statuses["in_review"]:
        raise HTTPException(status_code=409, detail={"code": codes["review_state_invalid"]})
    if user.id not in strategy.get("reviewer_ids", []):
        raise HTTPException(
            status_code=403, detail={"code": codes["review_assignment_required"]}
        )
    if user.id == strategy.get("created_by"):
        raise HTTPException(
            status_code=403, detail={"code": codes["self_review_not_allowed"]}
        )
    entry = {"reviewer_id": user.id, "note": payload.note, "at": now()}
    updated = await test_strategy_repository.update(
        strategy_id,
        strategy["project_id"],
        payload.expected_revision,
        {statuses["in_review"]},
        {
            "reviewed_by": list(dict.fromkeys([*strategy.get("reviewed_by", []), user.id])),
            "review_history": [*strategy.get("review_history", []), entry],
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["reviewed"],
        policy["entity_type"],
        strategy_id,
        strategy["project_id"],
        {"note": payload.note},
    )
    return updated


async def compare_strategies(strategy_id, other_strategy_id, user):
    policy = STRATEGY_POLICY
    left = await get_strategy_for_user(
        strategy_id, user, policy["permissions"]["read_version"]
    )
    right = await get_strategy_for_user(
        other_strategy_id, user, policy["permissions"]["read_version"]
    )
    if left["project_id"] != right["project_id"]:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["error_codes"]["cross_project_reference"]},
        )
    return compare_strategy_snapshots(left, right)


async def clone_strategy(project_id, payload, user):
    policy = STRATEGY_POLICY
    await get_project(project_id, user, policy["permissions"]["create"])
    source = await get_strategy_for_user(
        payload.source_strategy_id, user, policy["permissions"]["read"]
    )
    timestamp = now()
    strategy_id = new_id(policy["id_prefix"])
    fields = {field: source.get(field) for field in TestStrategyFields.model_fields}
    fields["name"] = payload.name
    fields["tailoring_rationale"] = payload.tailoring_rationale
    value = {
        "_id": strategy_id,
        "lineage_id": strategy_id,
        "project_id": project_id,
        "key": payload.key,
        **fields,
        "version": policy["initial_version"],
        "status": policy["statuses"]["draft"],
        "active_approved": False,
        "reviewed_by": [],
        "approval_history": [],
        "cloned_from_strategy_id": source["_id"],
        "cloned_from_project_id": source["project_id"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await test_strategy_repository.create(value)
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["key_version_exists"]},
        ) from error
    await audit(
        user.id,
        policy["events"]["cloned"],
        policy["entity_type"],
        strategy_id,
        project_id,
        {"source_strategy_id": source["_id"]},
    )
    return value


async def archive_strategy(strategy_id, payload, user):
    policy = STRATEGY_POLICY
    strategy = await get_strategy_for_user(
        strategy_id, user, policy["permissions"]["archive"]
    )
    updated = await test_strategy_repository.update(
        strategy_id,
        strategy["project_id"],
        payload.expected_revision,
        set(policy["archive_source_statuses"]),
        {
            "status": policy["statuses"]["archived"],
            "active_approved": False,
            "archived_by": user.id,
            "archived_at": now(),
            "archive_reason": payload.note,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["archive_conflict"]},
        )
    await audit(
        user.id,
        policy["events"]["archived"],
        policy["entity_type"],
        strategy_id,
        strategy["project_id"],
        {"reason": payload.note},
    )
    return updated
