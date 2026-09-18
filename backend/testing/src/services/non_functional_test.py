from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now


def normalize_plan(value):
    if value is None:
        return value
    normalized = dict(value)
    normalized["test_conditions"] = normalized.get(
        "test_conditions", normalized.get("test_condition_ids", [])
    )
    normalized["test_cases"] = normalized.get(
        "test_cases", normalized.get("test_case_version_ids", [])
    )
    normalized["requirement_refs"] = normalized.get(
        "requirement_refs", normalized.get("requirement_version_ids", [])
    )
    normalized["tool_refs"] = normalized.get("tool_refs", normalized.get("tools", []))
    return normalized


async def validate_refs(db, project_id, values):
    mappings = {
        "test_conditions": "test_conditions",
        "test_cases": "test_case_versions",
        "requirement_refs": "requirement_versions",
        "source_ai_result_ids": "ai_results",
    }
    for field, collection_name in mappings.items():
        ids = list(dict.fromkeys(values.get(field) or []))
        if ids and await getattr(db, collection_name).count_documents(
            {"project_id": project_id, "_id": {"$in": ids}}
        ) != len(ids):
            raise HTTPException(
                status_code=422, detail={"code": "NFR_TRACE_NOT_IN_PROJECT", "field": field}
            )


async def get_plan(db, plan_id, user, permission="nfrtest.read"):
    value = await db.non_functional_test_plans.find_one({"_id": plan_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, permission)
    return normalize_plan(value)


async def list_plans(db, project_id, plan_type, user):
    await get_project(project_id, user, "nfrtest.read")
    query = {"project_id": project_id}
    if plan_type:
        query["plan_type"] = plan_type
    items = [
        normalize_plan(item)
        for item in await db.non_functional_test_plans.find(query)
        .sort("updated_at", -1)
        .to_list(1000)
    ]
    return {"items": items, "total": len(items)}


async def create_plan(db, project_id, payload, user):
    await get_project(project_id, user, "nfrtest.manage")
    await validate_refs(db, project_id, payload.model_dump())
    if payload.idempotency_key:
        existing = await db.non_functional_test_plans.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            if (
                existing.get("plan_type") != payload.plan_type
                or existing.get("name") != payload.name
            ):
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    timestamp = now()
    value = {
        "_id": new_id("NFR"),
        "project_id": project_id,
        **payload.model_dump(),
        "external_evidence_ids": [],
        "status": "DRAFT",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await db.non_functional_test_plans.insert_one(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.non_functional_test_plans.find_one(
                {"project_id": project_id, "idempotency_key": payload.idempotency_key}
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


async def update_plan(db, plan_id, payload, user):
    value = await get_plan(db, plan_id, user, "nfrtest.manage")
    if value["status"] not in {"DRAFT", "IN_REVIEW"}:
        raise HTTPException(status_code=409, detail={"code": "APPROVED_NFR_PLAN_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    await validate_refs(db, value["project_id"], changes)
    merged = normalize_plan({**value, **changes})
    if not merged.get("test_conditions") and not merged.get("test_cases"):
        raise HTTPException(status_code=422, detail={"code": "NFR_TRACE_REQUIRED"})
    changes["updated_at"] = now()
    updated = await db.non_functional_test_plans.find_one_and_update(
        {
            "_id": plan_id,
            "revision": payload.expected_revision,
            "status": {"$in": ["DRAFT", "IN_REVIEW"]},
        },
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "nfr_test_plan_updated",
        "NonFunctionalTestPlan",
        plan_id,
        value["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def transition_plan(db, plan_id, payload, user, approve=False):
    permission = "nfrtest.approve" if approve else "nfrtest.review"
    value = await get_plan(db, plan_id, user, permission)
    source, target = ("IN_REVIEW", "APPROVED") if approve else ("DRAFT", "IN_REVIEW")
    if value["status"] != source:
        raise HTTPException(status_code=409, detail={"code": "INVALID_NFR_PLAN_TRANSITION"})
    timestamp = now()
    changes = {"status": target, "updated_at": timestamp, "transition_note": payload.note}
    if approve:
        changes.update({"approved_by": user.id, "approved_at": timestamp})
    else:
        changes.update({"submitted_by": user.id, "submitted_at": timestamp})
    updated = await db.non_functional_test_plans.find_one_and_update(
        {"_id": plan_id, "revision": payload.expected_revision, "status": source},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "nfr_test_plan_approved" if approve else "nfr_test_plan_submitted",
        "NonFunctionalTestPlan",
        plan_id,
        value["project_id"],
        {"note": payload.note},
    )
    return updated


async def import_evidence(db, plan_id, payload, user):
    value = await get_plan(db, plan_id, user, "nfrtest.evidence.import")
    existing = await db.non_functional_test_evidence.find_one(
        {"project_id": value["project_id"], "idempotency_key": payload.idempotency_key}
    )
    if existing:
        if existing["plan_id"] != plan_id or existing["raw_result_hash"] != payload.raw_result_hash:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return existing
    timestamp = now()
    evidence = {
        "_id": new_id("NFREVD"),
        "project_id": value["project_id"],
        "plan_id": plan_id,
        **payload.model_dump(),
        "imported_by": user.id,
        "created_at": timestamp,
    }
    try:
        await db.non_functional_test_evidence.insert_one(evidence)
    except DuplicateKeyError:
        return await db.non_functional_test_evidence.find_one(
            {"project_id": value["project_id"], "idempotency_key": payload.idempotency_key}
        )
    await db.non_functional_test_plans.update_one(
        {"_id": plan_id},
        {
            "$addToSet": {"external_evidence_ids": evidence["_id"]},
            "$set": {"result_summary": payload.result_summary, "updated_at": timestamp},
            "$inc": {"revision": 1},
        },
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
