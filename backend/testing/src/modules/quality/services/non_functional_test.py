from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.repositories.non_functional_test import non_functional_test_repository
from src.services.domain_policy import domain_policy


NON_FUNCTIONAL_TEST_POLICY = domain_policy("non_functional_test")


def normalize_plan(value):
    if value is None:
        return value
    normalized = dict(value)
    for target, source in NON_FUNCTIONAL_TEST_POLICY["field_aliases"].items():
        normalized[target] = normalized.get(target, normalized.get(source, []))
    return normalized


async def validate_refs(project_id, values):
    mappings = NON_FUNCTIONAL_TEST_POLICY["reference_collections"]
    for field, collection_name in mappings.items():
        ids = list(dict.fromkeys(values.get(field) or []))
        if ids and await non_functional_test_repository.count_project_entities(
            collection_name, project_id, ids
        ) != len(ids):
            raise HTTPException(
                status_code=422,
                detail={"code": NON_FUNCTIONAL_TEST_POLICY["trace_not_in_project_code"], "field": field},
            )


async def get_plan(plan_id, user, permission="nfrtest.read"):
    value = await non_functional_test_repository.find_plan(plan_id)
    if not value:
        raise HTTPException(
            status_code=404,
            detail={"code": NON_FUNCTIONAL_TEST_POLICY["entity_not_found_code"]},
        )
    await get_project(value["project_id"], user, permission)
    return normalize_plan(value)


async def list_plans(project_id, plan_type, user):
    await get_project(project_id, user, "nfrtest.read")
    query = {"project_id": project_id}
    if plan_type:
        query["plan_type"] = plan_type
    items = [
        normalize_plan(item)
        for item in await non_functional_test_repository.list_plans(
            query, domain_policy("non_functional_test")["list_limit"]
        )
    ]
    return {"items": items, "total": len(items)}


async def create_plan(project_id, payload, user):
    policy = domain_policy("non_functional_test")
    await get_project(project_id, user, "nfrtest.manage")
    await validate_refs(project_id, payload.model_dump())
    if payload.idempotency_key:
        existing = await non_functional_test_repository.find_plan_by_idempotency_key(
            project_id, payload.idempotency_key
        )
        if existing:
            if (
                existing.get("plan_type") != payload.plan_type
                or existing.get("name") != payload.name
            ):
                raise HTTPException(
                    status_code=409, detail={"code": policy["idempotency_reused_code"]}
                )
            return existing
    timestamp = now()
    value = {
        "_id": new_id(policy["plan_id_prefix"]),
        "project_id": project_id,
        **payload.model_dump(),
        "external_evidence_ids": [],
        "status": policy["draft_status"],
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await non_functional_test_repository.insert_plan(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await non_functional_test_repository.find_plan_by_idempotency_key(
                project_id, payload.idempotency_key
            )
        raise
    await audit(
        user.id,
        "nfr_test_plan_created",
        "NonFunctionalTestPlan",
        value["_id"],
        project_id,
        {"plan_type": value["plan_type"]},
    )
    return value


async def update_plan(plan_id, payload, user):
    policy = domain_policy("non_functional_test")
    value = await get_plan(plan_id, user, "nfrtest.manage")
    if value["status"] not in policy["editable_statuses"]:
        raise HTTPException(status_code=409, detail={"code": policy["approved_immutable_code"]})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    await validate_refs(value["project_id"], changes)
    merged = normalize_plan({**value, **changes})
    if not merged.get("test_conditions") and not merged.get("test_cases"):
        raise HTTPException(status_code=422, detail={"code": policy["trace_required_code"]})
    changes["updated_at"] = now()
    updated = await non_functional_test_repository.update_plan(
        plan_id, payload.expected_revision, policy["editable_statuses"], changes
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        "nfr_test_plan_updated",
        "NonFunctionalTestPlan",
        plan_id,
        value["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def transition_plan(plan_id, payload, user, approve=False):
    policy = domain_policy("non_functional_test")
    permission = "nfrtest.approve" if approve else "nfrtest.review"
    value = await get_plan(plan_id, user, permission)
    transition = policy["transitions"]["approve" if approve else "submit"]
    source, target = transition["source"], transition["target"]
    if value["status"] != source:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    timestamp = now()
    changes = {"status": target, "updated_at": timestamp, "transition_note": payload.note}
    if approve:
        changes.update({"approved_by": user.id, "approved_at": timestamp})
    else:
        changes.update({"submitted_by": user.id, "submitted_at": timestamp})
    updated = await non_functional_test_repository.transition_plan(
        plan_id, payload.expected_revision, source, changes
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        "nfr_test_plan_approved" if approve else "nfr_test_plan_submitted",
        "NonFunctionalTestPlan",
        plan_id,
        value["project_id"],
        {"note": payload.note},
    )
    return updated


async def import_evidence(plan_id, payload, user):
    policy = domain_policy("non_functional_test")
    value = await get_plan(plan_id, user, "nfrtest.evidence.import")
    existing = await non_functional_test_repository.find_evidence_by_idempotency_key(
        value["project_id"], payload.idempotency_key
    )
    if existing:
        if existing["plan_id"] != plan_id or existing["raw_result_hash"] != payload.raw_result_hash:
            raise HTTPException(
                status_code=409, detail={"code": policy["idempotency_reused_code"]}
            )
        return existing
    timestamp = now()
    evidence = {
        "_id": new_id(policy["evidence_id_prefix"]),
        "project_id": value["project_id"],
        "plan_id": plan_id,
        **payload.model_dump(),
        "imported_by": user.id,
        "created_at": timestamp,
    }
    try:
        await non_functional_test_repository.insert_evidence(evidence)
    except DuplicateKeyError:
        return await non_functional_test_repository.find_evidence_by_idempotency_key(
            value["project_id"], payload.idempotency_key
        )
    await non_functional_test_repository.attach_evidence(
        plan_id, evidence["_id"], payload.result_summary, timestamp
    )
    await audit(
        user.id,
        "nfr_external_evidence_imported",
        "NonFunctionalTestEvidence",
        evidence["_id"],
        value["project_id"],
        {
            "plan_id": plan_id,
            "provider": payload.provider,
            "raw_result_hash": payload.raw_result_hash,
        },
    )
    return evidence


class NonFunctionalTestService:
    @staticmethod
    async def list(project_id, plan_type, user):
        return await list_plans(project_id, plan_type, user)

    @staticmethod
    async def create(project_id, payload, user):
        return await create_plan(project_id, payload, user)

    @staticmethod
    async def get(plan_id, user):
        value = await get_plan(plan_id, user)
        value["external_evidence"] = await non_functional_test_repository.list_evidence(
            plan_id, domain_policy("non_functional_test")["evidence_list_limit"]
        )
        return value

    @staticmethod
    async def update(plan_id, payload, user):
        return await update_plan(plan_id, payload, user)

    @staticmethod
    async def transition(plan_id, payload, user, approve=False):
        return await transition_plan(plan_id, payload, user, approve)

    @staticmethod
    async def import_evidence(plan_id, payload, user):
        return await import_evidence(plan_id, payload, user)
