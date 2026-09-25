import hashlib

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import (
    audit,
    envelope,
    get_project,
    new_id,
    next_key,
    now,
    plain_text,
    validate_doc,
)
from src.repositories.requirement import requirement_repository
from src.services.domain_policy import domain_policy
from src.services.requirement_indexing import (
    index_requirement_version,
    validate_requirement_sources,
)
from src.services.requirement_workflow import serialized_content

TRANSFORMATION_POLICY = domain_policy("requirement_transformations")


def unique_source_refs(values):
    result = []
    seen = set()
    for value in values:
        marker = serialized_content(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


async def find_requirement_transformation(project_id, idempotency_key):
    return await requirement_repository.find_transformation(project_id, idempotency_key)


async def load_requirement_baselines(
    project_id, requirement_ids, expected_version_ids, user, permission
):
    await get_project(project_id, user, permission)
    ordered_ids = list(dict.fromkeys(requirement_ids))
    if len(ordered_ids) != len(requirement_ids):
        raise HTTPException(status_code=422, detail={"code": TRANSFORMATION_POLICY["duplicate_source_code"]})
    if set(expected_version_ids) != set(ordered_ids):
        raise HTTPException(status_code=422, detail={"code": TRANSFORMATION_POLICY["source_version_set_mismatch_code"]})
    requirements = await requirement_repository.list_requirements_by_ids(
        project_id, ordered_ids, len(ordered_ids)
    )
    by_id = {item["_id"]: item for item in requirements}
    if set(by_id) != set(ordered_ids):
        raise HTTPException(status_code=404, detail={"code": TRANSFORMATION_POLICY["source_not_found_code"]})
    version_ids = list(expected_version_ids.values())
    versions = await requirement_repository.list_versions_by_ids(
        project_id, version_ids, len(version_ids)
    )
    versions_by_id = {item["_id"]: item for item in versions}
    if set(versions_by_id) != set(version_ids):
        raise HTTPException(
            status_code=404, detail={"code": TRANSFORMATION_POLICY["source_version_not_found_code"]}
        )
    sources = []
    for requirement_id in ordered_ids:
        requirement = by_id[requirement_id]
        version_id = expected_version_ids[requirement_id]
        version = versions_by_id[version_id]
        if requirement.get("current_version_id") != version_id:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": TRANSFORMATION_POLICY["stale_source_code"],
                    "requirement_id": requirement_id,
                    "current_version_id": requirement.get("current_version_id"),
                },
            )
        if (
            requirement.get("status") != TRANSFORMATION_POLICY["baselined_status"]
            or version.get("status") != TRANSFORMATION_POLICY["baselined_status"]
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": TRANSFORMATION_POLICY["source_not_baselined_code"],
                    "requirement_id": requirement_id,
                },
            )
        sources.append((requirement, version))
    return sources


async def claim_requirement_transformation(
    project_id, transformation_type, payload, source_requirement_ids, source_version_ids, user
):
    request_payload = payload.model_dump(mode="json")
    request_fingerprint = hashlib.sha256(
        serialized_content(
            {key: value for key, value in request_payload.items() if key != "idempotency_key"}
        ).encode("utf-8")
    ).hexdigest()
    existing = await requirement_repository.find_transformation(
        project_id, payload.idempotency_key
    )
    if existing:
        if existing.get("request_fingerprint") != request_fingerprint:
            raise HTTPException(status_code=409, detail={"code": TRANSFORMATION_POLICY["idempotency_reused_code"]})
        if existing.get("status") == TRANSFORMATION_POLICY["confirmed_status"]:
            return existing, False
        if existing.get("status") == TRANSFORMATION_POLICY["confirming_status"]:
            raise HTTPException(
                status_code=409, detail={"code": TRANSFORMATION_POLICY["in_progress_code"]}
            )
        claimed = await requirement_repository.claim_failed_transformation(
            existing["_id"],
            project_id,
            TRANSFORMATION_POLICY["failed_status"],
            TRANSFORMATION_POLICY["confirming_status"],
            now(),
        )
        if not claimed:
            raise HTTPException(
                status_code=409, detail={"code": TRANSFORMATION_POLICY["conflict_code"]}
            )
        return claimed, True
    timestamp = now()
    transformation = {
        "_id": new_id(TRANSFORMATION_POLICY["transformation_id_prefix"]),
        "project_id": project_id,
        "type": transformation_type,
        "source_requirement_ids": source_requirement_ids,
        "source_version_ids": source_version_ids,
        "result_requirement_ids": [],
        "result_version_ids": [],
        "reason": payload.reason,
        "idempotency_key": payload.idempotency_key,
        "request_fingerprint": request_fingerprint,
        "status": TRANSFORMATION_POLICY["confirming_status"],
        "attempt": TRANSFORMATION_POLICY["initial_attempt"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await requirement_repository.insert_transformation(transformation)
    except DuplicateKeyError:
        existing = await requirement_repository.find_transformation(
            project_id, payload.idempotency_key
        )
        if (
            existing
            and existing.get("request_fingerprint") == request_fingerprint
            and existing.get("status") == TRANSFORMATION_POLICY["confirmed_status"]
        ):
            return existing, False
        raise HTTPException(status_code=409, detail={"code": TRANSFORMATION_POLICY["conflict_code"]})
    return transformation, True


async def prepare_requirement_output(
    project_id, draft, user, transformation, index, sources, relation
):
    validate_doc(draft.content_doc)
    keys = [item.key for item in draft.acceptance_criteria]
    if len(keys) != len(set(keys)):
        raise HTTPException(status_code=422, detail={"code": TRANSFORMATION_POLICY["duplicate_criterion_key_code"]})
    for item in draft.acceptance_criteria:
        validate_doc(item.content_doc)
    source_refs = unique_source_refs(
        list(draft.source_refs)
        + [
            {
                "type": TRANSFORMATION_POLICY["requirement_source_type"],
                "requirement_id": requirement["_id"],
                "requirement_version_id": version["_id"],
                "relation": relation,
            }
            for requirement, version in sources
        ]
    )
    await validate_requirement_sources(project_id, source_refs)
    timestamp = now()
    requirement_id = f"{transformation['_id']}-{TRANSFORMATION_POLICY['requirement_id_segment']}-{index + 1}"
    version_id = f"{transformation['_id']}-{TRANSFORMATION_POLICY['version_id_segment']}-{index + 1}"
    requirement_key = draft.requirement_key or await next_key(
        project_id,
        TRANSFORMATION_POLICY["requirement_counter"],
        TRANSFORMATION_POLICY["requirement_key_prefix"],
    )
    version = {
        "_id": version_id,
        "project_id": project_id,
        "requirement_id": requirement_id,
        "requirement_key": requirement_key,
        "version": TRANSFORMATION_POLICY["initial_version"],
        "title": draft.title,
        "type": draft.type,
        "priority": draft.priority,
        "risk": draft.risk,
        "content_doc": draft.content_doc,
        "plain_text_projection": plain_text(draft.content_doc),
        "business_rules": draft.business_rules,
        "actors": draft.actors,
        "dependencies": draft.dependencies,
        "source_refs": source_refs,
        "tags": draft.tags,
        "owner_id": draft.owner_id or user.id,
        "acceptance_criterion_ids": [],
        "parent_version_id": None,
        "change_reason": transformation["reason"],
        "status": TRANSFORMATION_POLICY["draft_status"],
        "revision": TRANSFORMATION_POLICY["initial_revision"],
        "origin": relation,
        "transformation_id": transformation["_id"],
        "derived_from": [
            {"requirement_id": requirement["_id"], "requirement_version_id": source["_id"]}
            for requirement, source in sources
        ],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    criteria = []
    for criterion_index, value in enumerate(draft.acceptance_criteria):
        item = value.model_dump()
        item["status"] = TRANSFORMATION_POLICY["criterion_draft_status"]
        criterion = {
            "_id": f"{transformation['_id']}-{TRANSFORMATION_POLICY['criterion_id_segment']}-{index + 1}-{criterion_index + 1}",
            "project_id": project_id,
            "requirement_version_id": version_id,
            **item,
            "plain_text": plain_text(item["content_doc"]),
            "created_at": timestamp,
        }
        criteria.append(criterion)
    version["acceptance_criterion_ids"] = [item["_id"] for item in criteria]
    requirement = {
        "_id": requirement_id,
        "project_id": project_id,
        "requirement_key": requirement_key,
        "current_version_id": version_id,
        "status": TRANSFORMATION_POLICY["draft_status"],
        "owner_id": draft.owner_id or user.id,
        "tags": draft.tags,
        "transformation_id": transformation["_id"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    return requirement, version, criteria


async def hydrate_requirement_transformation(transformation):
    requirements = await requirement_repository.list_requirements_by_ids(
        transformation["project_id"],
        transformation.get("result_requirement_ids", []),
        TRANSFORMATION_POLICY["hydration_limit"],
    )
    versions = await requirement_repository.list_versions_by_ids(
        transformation["project_id"],
        transformation.get("result_version_ids", []),
        TRANSFORMATION_POLICY["hydration_limit"],
    )
    versions_by_id = {item["_id"]: item for item in versions}
    return {
        "transformation": transformation,
        "requirements": [
            {**item, "current_version": versions_by_id.get(item.get("current_version_id"))}
            for item in requirements
        ],
    }


async def execute_requirement_transformation(
    project_id, transformation, sources, drafts, user, relation
):
    output_requirements = []
    output_versions = []
    output_criteria = []
    updated_sources = []
    try:
        for index, draft in enumerate(drafts):
            requirement, version, criteria = await prepare_requirement_output(
                project_id, draft, user, transformation, index, sources, relation
            )
            output_requirements.append(requirement)
            output_versions.append(version)
            output_criteria.extend(criteria)
        keys = [item["requirement_key"] for item in output_requirements]
        if len(keys) != len(set(keys)):
            raise HTTPException(
                status_code=422, detail={"code": TRANSFORMATION_POLICY["duplicate_output_key_code"]}
            )
        await requirement_repository.insert_outputs(
            output_requirements, output_versions, output_criteria
        )
        result_ids = [item["_id"] for item in output_requirements]
        for source_requirement, source_version in sources:
            timestamp = now()
            version_updated = await requirement_repository.supersede_version(
                source_version["_id"],
                project_id,
                TRANSFORMATION_POLICY["baselined_status"],
                TRANSFORMATION_POLICY["superseded_status"],
                result_ids,
                transformation["_id"],
                user.id,
                timestamp,
            )
            if not version_updated:
                raise HTTPException(status_code=409, detail={"code": TRANSFORMATION_POLICY["stale_source_code"]})
            updated_sources.append((source_requirement["_id"], source_version["_id"]))
            requirement_updated = await requirement_repository.supersede_requirement(
                source_requirement["_id"],
                source_version["_id"],
                project_id,
                TRANSFORMATION_POLICY["baselined_status"],
                TRANSFORMATION_POLICY["superseded_status"],
                result_ids,
                transformation["_id"],
                user.id,
                timestamp,
            )
            if not requirement_updated:
                raise HTTPException(status_code=409, detail={"code": TRANSFORMATION_POLICY["stale_source_code"]})
        transformation = await requirement_repository.confirm_transformation(
            transformation["_id"],
            project_id,
            TRANSFORMATION_POLICY["confirming_status"],
            TRANSFORMATION_POLICY["confirmed_status"],
            result_ids,
            [item["_id"] for item in output_versions],
            now(),
        )
        if not transformation:
            raise HTTPException(
                status_code=409, detail={"code": TRANSFORMATION_POLICY["conflict_code"]}
            )
    except Exception as error:
        for requirement_id, version_id in updated_sources:
            await requirement_repository.rollback_superseded_source(
                requirement_id,
                version_id,
                project_id,
                transformation["_id"],
                TRANSFORMATION_POLICY["baselined_status"],
                now(),
            )
        await requirement_repository.discard_transformation_outputs(
            project_id,
            transformation["_id"],
            [item["_id"] for item in output_criteria],
        )
        await requirement_repository.fail_transformation(
            transformation["_id"],
            project_id,
            TRANSFORMATION_POLICY["failed_status"],
            getattr(error, "detail", {"code": type(error).__name__}),
            now(),
        )
        raise
    indexed = [await index_requirement_version(version) for version in output_versions]
    await audit(
        user.id,
        TRANSFORMATION_POLICY["relation_events"][relation],
        TRANSFORMATION_POLICY["transformation_entity"],
        transformation["_id"],
        project_id,
        {
            "source_requirement_ids": transformation["source_requirement_ids"],
            "result_requirement_ids": transformation["result_requirement_ids"],
            "reason": transformation["reason"],
        },
    )
    result = await hydrate_requirement_transformation(transformation)
    return envelope(
        result,
        status=TRANSFORMATION_POLICY["success_status"] if all(indexed) else TRANSFORMATION_POLICY["degraded_status"],
        degraded_mode=None if all(indexed) else TRANSFORMATION_POLICY["degraded_vector_mode"],
    )
